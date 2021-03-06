package manager

import (
	"errors"
	"fmt"
	"strconv"
)

type SimpleManager struct {
	component ManagerComponent
}

func (m *SimpleManager) Initalize(component ManagerComponent) {
	m.component = component
}

// Get a single thing by id
func (m *SimpleManager) Get(id uint64) (Thing, error) {
	thing, err := m.component.Load(id)
	if err == nil && thing != nil {
		if err := thing.Check(); err != nil {
			return nil, err
		}
		err = m.component.AfterLoad(thing)
	}
	return thing, err
}

func (m *SimpleManager) Find(params interface{}) ([]Thing, error) {
	// create empty array so we return [] not null
	things := []Thing{}
	ids, err := m.component.Find(params)
	if err != nil {
		return nil, err
	}
	for _, id := range ids {
		thing, err2 := m.Get(id)
		if err2 == nil {
			things = append(things, thing)
		} else {
			fmt.Println(id, err2.Error())
		}
	}
	return things, err
}

func (m *SimpleManager) New(thing Thing) error {
	if err := thing.Check(); err != nil {
		return err
	}
	existingID, err := m.component.FindExisting(thing)
	if err != nil {
		return err
	} else if existingID > 0 {
		existing, err := m.Get(existingID)
		if err != nil {
			return err
		}
		existing.Merge(thing)
		m.Save(existing)
	} else {
		return m.component.Create(thing)
	}
	return nil
}

func (m *SimpleManager) Save(thing Thing) error {
	if err := thing.Check(); err != nil {
		return err
	}
	_, err := m.Get(thing.GetID())
	if err != nil {
		return errors.New("Error loading existing " + thing.Type() + " from id " + strconv.FormatUint(thing.GetID(), 10))
	}
	return m.component.Update(thing)
}

func (m *SimpleManager) Merge(thing, thingToMerge Thing, params string) error {
	return errors.New("Not implemented")
}

func (m *SimpleManager) Delete(thing Thing) error {
	return errors.New("Not implemented")
}

// overwrite the existing version of the thing with the new version provided to it
func (m *SimpleManager) Overwrite(thing Thing) (Thing, error) {
	if err := thing.Check(); err != nil {
		return nil, err
	}
	oldThing, err := m.Get(thing.GetID())
	if err != nil {
		return nil, errors.New("Error loading existing " + thing.Type())
	}
	oldThing.Overwrite(thing)
	return oldThing, m.Save(oldThing)
}

func (m *SimpleManager) NewThing() Thing {
	return m.component.NewThing()
}

func (m *SimpleManager) Process(id uint64) {
	m.component.Process(id)
}

func (m *SimpleManager) LoadDeps(id uint64) {
	thing, err := m.Get(id)
	if err != nil {
		fmt.Println(err)
		return
	}
	err = m.component.AfterLoad(thing)
	if err != nil {
		fmt.Println(err)
	}
}
