#
#===============================================================================
#
#         FILE: Classifier.pm
#
#  DESCRIPTION: Class to manage the classification of new expense items
#
#        FILES: ---
#         BUGS: ---
#        NOTES: ---
#       AUTHOR: Timothy Moll
# ORGANIZATION: 
#      VERSION: 0.1
#      CREATED: 23/12/14 21:21:06
#     REVISION: ---
#===============================================================================

package Classifier;
use Moose;

use strict;
use warnings;

use ExpenseData::Processors::Processor;
use ExpenseData::Processors::Processor_AMEX;
use ExpenseData::Processors::Processor_Aqua;
use ExpenseData::Processors::Processor_Nationwide;
use ExpenseData::Processors::Processor_Generic;
use DataTypes::Expense;
use AutomaticClassifier;
 
has 'expensesDB' => (is => 'rw', required => 1); 
has 'expenseDB' => (is => 'rw', required => 1); 
has 'classifications' => ( is => 'rw', writer => 'setClassifications' );
has 'incoming_classifications' => ( is => 'ro', isa => 'HashRef', default=> sub { my %empty; return \%empty}, reader=>'getIncomingClassifications');

sub BUILD
{
	my $self = shift;
	$self->setClassifications($self->expensesDB->getCurrentClassifications());
	my $classifications = $self->getIncomingClassifications();
	if( open(my $file, '<', 'in/classifications.csv') )
	{
		foreach (<$file>)
		{
			chomp;
			my @lineParts = split(/\|/,$_);
			$classifications->{$lineParts[0]} = $lineParts[1];
		}	
		close ($file);
	}
}

sub processUnclassified
{
	my ($self) = @_;
	my $results = $self->expensesDB->getUnclassifiedLines();
	foreach (@$results)
	{
		my $expense = $_->[0]->processRawLine($_->[1], $_->[2], $_->[3], $_->[4]);
		my $preClassification = $self->getIncomingClassifications()->{$_->[1]};
		if ((defined $expense->getClassification)) {
		} elsif (defined $preClassification)
		{
			if ($self->textMatchClassification($preClassification))
			{
				my $results = ($self->textMatchClassification($preClassification));
	            if (scalar @$results == 1 )
		        {
			        print $expense->getDescription,' classified as: ',$self->classifications->{$$results[0]},"\n\n";
				    $expense->setClassification($$results[0]);
				} else {
	                print "Multiple possible classification matches:\n";
		            foreach (@$results)
			        {
				        print "   ",
					          $self->classifications->{$_},
						      "\n"
					}
				}
			} else {
				print "**** Invalid classification: $preClassification\n\n";
			}
			
		} else {
			my $autoClass = AutomaticClassifier->new(numbers => $self->expensesDB());
			$autoClass->classify($expense);
#			$self->getClassification($expense);
		}

		$self->expenseDB->saveExpense($expense) if (defined $expense->getClassification());

	}
}

sub validateClassification
{
    my ($self, $value) = @_;
    my $classifications = $self->classifications();
    return 0 if ($value eq "");
    return 1 if (exists $$classifications{$value});
    return 0;
}

sub textMatchClassification
{
    my ($self, $text) = @_;
    my $classifications = $self->classifications();
    return 0 if ($text eq "");
    $text = uc $text;
    my @results;
    foreach (keys %$classifications)
    {
        my $value = uc $$classifications{$_};
        if ($value =~ m/^$text$/)
        {
            my @singleResult;
            push (@singleResult, $_);
            return \@singleResult;
        }
        else
        {
            push(@results, $_) if ($value =~ m/$text/);
            push(@results, $_) if ($text =~ m/$value/);
        }
    }
    return 0 unless (scalar @results);
    return \@results;
}

sub getClassification
{
    my ($self, $record) = @_;
    while(1)
    {
        print    "Enter classification for: \n",
#                 '  -- ',$record->getAccountName,
                 "\n  -- ",$record->getDescription,
                 "\n  -- ",$record->getDate,
                 '  --  £',$record->getAmount,
                 "\n  > ";
        my $value =<>;
        chomp ($value);
        if ($self->validateClassification($value))
        {
            print "Classified as: ",$self->classifications->{$value},"\n\n";
            $record->setClassification($value);
            return 1;
        } elsif ($value eq 'CHANGE VALUE') {
            my $continue = 1;
            while($continue)
            {
                print "\nEnter new amount:\n  > ";
                $value =<>;
                chomp $value;
                if ($value =~ m/^[0-9.]*$/)
                {
                    $record->setAmount($value);
                    print "\n\n";
                    $continue = 0;
                } else {
                    print "**** >$value< is an invalid amount\n";
                }
            }
        } elsif ($self->textMatchClassification($value)) {
            my $results = ($self->textMatchClassification($value));
            if (scalar @$results == 1 )
            {
                print "Classified as: ",$self->classifications->{$$results[0]},"\n\n";
                $record->setClassification($$results[0]);
                return 1;
            }
            else
            {
                print "Multiple possible classification matches:\n";
                foreach (@$results)
                {
                    print "   ",
                          $self->classifications->{$_},
                          "\n"
                }
            }
        } else {
            print "**** Invalid classification: $value\n\n";
        }
    }
}

1;

