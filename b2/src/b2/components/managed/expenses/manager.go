package expenses

import (
	"b2/backend"
	"b2/components/managed/docexmappings"
	"b2/manager"
	"errors"
	"fmt"
	"github.com/gorilla/schema"
	"math"
	"net/url"
	"regexp"
	"strings"
)

type Query struct {
	From           string   `schema:"from"`
	To             string   `schema:"to"`
	Date           string   `schema:"date"`
	Search         string   `schema:"search"`
	Dates          []string `schema:"dates"`
	Classification string   `schema:"classification"`
}

func cleanQuery(query *Query) {
	classRE := regexp.MustCompile(`clas[sifcaton]{0,10}: *(?:"([^"]*)"|([^ ]*))`)
	value := classRE.FindStringSubmatch(query.Search)
	if len(value) >= 3 {
		// add them together as either the first or second match should be empty
		query.Classification = value[1] + value[2]
		query.Search = classRE.ReplaceAllString(query.Search, "$1")
	}
}

type ExManager struct {
	backend *backend.Backend
}

func Instance(backend *backend.Backend) manager.Manager {
	em := new(ExManager)
	em.backend = backend
	general := new(manager.CachingManager)
	general.Initalize(em)
	return general
}

func (em *ExManager) Load(eid uint64) (manager.Thing, error) {
	expense, err := loadExpense(eid, em.backend.DB)
	if err != nil {
		return nil, err
	}
	if expense.Metadata.Classification == 0 {
		classifyExpense(expense, em.backend.DB)
		err = em.Update(expense)
	}
	return expense, err
}

func (em *ExManager) AfterLoad(ex manager.Thing) error {
	expense, ok := ex.(*Expense)
	if !ok {
		return errors.New("Non expense passed to function")
	}
	v := new(docexmappings.Query)
	v.ExpenseId = expense.ID
	mapps, err := em.backend.Mappings.Find(v)
	expense.Lock()
	defer expense.Unlock()
	expense.Documents = []*docexmappings.Mapping{}
	for _, thing := range mapps {
		mapping, ok := thing.(*(docexmappings.Mapping))
		if !ok {
			return errors.New("Non mapping returned from function")
		}
		expense.Documents = append(expense.Documents, mapping)
	}
	return err
}

func (em *ExManager) Find(query interface{}) ([]uint64, error) {
	var search *Query
	switch query.(type) {
	case *Query:
		search = query.(*Query)
	case url.Values:
		search = new(Query)
		decoder := schema.NewDecoder()
		err := decoder.Decode(search, query.(url.Values))
		if err != nil {
			return nil, err
		}
	default:
		return nil, errors.New("Unknown type passed to find function")
	}
	cleanQuery(search)
	//if search.Classification != "" {
	//	return findExpensesClassification(search, em.backend.DB)
	//}
	return findExpenses(search, em.backend.DB)
}

func (em *ExManager) FindExisting(thing manager.Thing) (uint64, error) {
	var oldEid uint64 = 0
	var err error
	expense, ok := thing.(*Expense)
	if !ok {
		return 0, errors.New("Non expense passed to function")
	}
	expense.RLock()
	defer expense.RUnlock()
	if expense.TransactionReference != "" {
		oldEid, err = findExpenseByTranRef(expense.TransactionReference, expense.AccountID, em.backend.DB)
		if err != nil {
			return 0, err
		}
	} else if expense.Metadata.Temporary {
		oldEid, err = findExpenseByDetails(expense.Amount, expense.Date, expense.Description, expense.Currency, expense.AccountID, em.backend.DB)
		if err != nil {
			return 0, err
		}
	} else {
		// todo: improve matching (date range? tipping percent? ignore description spaces?)
		results, err := getTempExpenseDetails(expense.AccountID, em.backend.DB)
		if err != nil {
			return 0, err
		}
		lastDiff := 10000000.0
		confirmedTolerance := 0.05
		for _, result := range results {
			// check same sign
			if expense.Amount*result.Amount < 0 {
				continue
			}
			resAmt := float64(result.Amount)
			exAmt := float64(expense.Amount)
			diff := math.Abs(math.Abs(resAmt)-math.Abs(exAmt)) / math.Abs(exAmt)
			if diff > confirmedTolerance {
				continue
			}
			oldDesc := strings.ToLower(strings.Replace(expense.Description, " ", "", -1))
			newDesc := strings.ToLower(strings.Replace(result.Description, " ", "", -1))
			if oldDesc != newDesc {
				continue
			}
			if diff < lastDiff {
				oldEid = result.ID
				lastDiff = diff
			}
		}
	}
	// Logic for what to return is to make sure only a temporary expense is overwritten
	// and a duplicate expense is met with an error
	// | NewEx | OldEx | Return |
	// --------------------------
	// |  T    |  T    | EID    | Updating Temp
	// |  P    |  T    | EID    | Updating Temp to Permanent
	// |  T    |  P    | Err    | New Temp for Duplicate
	// |  P    |  P    | Err    | Duplicate
	if oldEid > 0 {
		oldEx, err := em.Load(oldEid)
		if err != nil {
			return 0, err
		}
		// if this can't be cast to an expense, something has gone very wrong
		if oldEx.(*Expense).Metadata.Temporary {
			return oldEid, nil
		} else if expense.Metadata.Temporary {
			return 0, errors.New(fmt.Sprintf("Could not create new temporary expense, as expense already exists as %d", oldEid))
		} else {
			return 0, errors.New(fmt.Sprintf("Could not create new expense, as expense already exists as %d", oldEid))
		}
	}
	return 0, nil
}

func (em *ExManager) Create(ex manager.Thing) error {
	expense, ok := ex.(*Expense)
	if !ok {
		return errors.New("Non expense passed to function")
	}
	classifyExpense(expense, em.backend.DB)
	return createExpense(expense, em.backend.DB)
}

func (em *ExManager) Combine(ex, ex2 manager.Thing, params string) error {
	expense, ok := ex.(*Expense)
	exMergeWith, ok2 := ex2.(*Expense)
	if !(ok && ok2) {
		return errors.New("Non expense passed to function")
	}
	if params == "commission" {
		expense.Commission += exMergeWith.Amount
		expense.Amount += exMergeWith.Amount
		expense.Metadata.OldValues += "Commission from: " + exMergeWith.Description + "\n"
		expense.Metadata.OldValues += fmt.Sprintf("Commission amount: %f\n", exMergeWith.Amount)
		expense.Metadata.OldValues += "Commission tranref: " + exMergeWith.TransactionReference + "\n"
		expense.Metadata.OldValues += "Commission date: " + exMergeWith.Date + "\n"
	} else {
		expense.Merge(exMergeWith)
	}
	exMergeWith.deleted = true
	for _, mapping := range exMergeWith.Documents {
		mapping.EID = expense.ID
		err := em.backend.Mappings.Save(mapping)
		if err != nil {
			fmt.Println(err)
		}
	}
	exMergeWith.Documents = nil
	expense.Documents = nil
	return em.AfterLoad(expense)
}

func (em *ExManager) Update(ex manager.Thing) error {
	expense, ok := ex.(*Expense)
	if !ok {
		return errors.New("Non expense passed to function")
	}
	return updateExpense(expense, em.backend.DB)
}

func (em *ExManager) Delete(ex manager.Thing) error {
	expense, ok := ex.(*Expense)
	if !ok {
		return errors.New("Non expense passed to function")
	}
	expense.Lock()
	defer expense.Unlock()
	err := deleteExpense(expense, em.backend.DB)
	if err != nil {
		return nil
	}
	expense.deleted = true
	for _, mapping := range expense.Documents {
		err = em.backend.Mappings.Delete(mapping)
		if err != nil {
			fmt.Println(err)
		}
	}
	return err
}

func (em *ExManager) NewThing() manager.Thing {
	return new(Expense)
}

func (em *ExManager) Process(id uint64) {
	ex, err := em.backend.Expenses.Get(id)
	if err != nil {
		fmt.Println(err)
		return
	}
	expense, ok := ex.(*Expense)
	if !ok {
		fmt.Println("Non expense passed to function")
		return
	}
	classifyExpense(expense, em.backend.DB)
	err = em.Update(expense)
	if err != nil {
		fmt.Println("Error updating expense")
	}
}
