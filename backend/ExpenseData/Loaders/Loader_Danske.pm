#!/usr/bin/perl

package Loader_Danske;
use Moose;
extends 'Loader';

use strict;
use warnings;

use WWW::Mechanize::Firefox;
use HTML::Form;

use DataTypes::GenericRawLine;

use Switch;

has 'UserName' => ( is => 'rw', isa=>'Str', writer=>'setUserName', reader=>'getUserName');
has 'Password' => ( is => 'rw', isa=>'Str', writer=>'setPassword', reader=>'getPassword');
has 'AccountName' => ( is => 'rw', isa=>'Str', writer=>'setAccountName', reader=>'getAccountName');

# build string formats:
# file; directory, filename
# notfile; username; password, accountname
sub BUILD
{
	my ($self) = @_;
	my @buildParts = split (';' ,$self->build_string);
	if ($buildParts[0])
	{
		$self->setUserName($buildParts[1]);
		$self->setPassword($buildParts[2]);
		$self->setAccountName($buildParts[3]);
	}
	else
	{
		$self->setDirectory($buildParts[1]);
		$self->setFileName($buildParts[2]);
	}
}

sub _proccessFile
{
	my ($self, $data) = @_;
	#print "looking at $filename\n";
	#chdir $self->getDirectory;
	#open (my $file, '<', $filename) or die "Cannot open file $filename\n";
	my $line = GenericRawLine->new();
	foreach ($_ =~ m/nytabellinie2\("(.*)", ?"(.*)", ?"(.*)"\)/g)
	{
		#if ($_ =~ m/nytabellinie2\("(.*)", ?"(.*)", ?"(.*)"\)/)
		#{
			my ($key, $value) = ($1, $2);
			switch ($key)
			{
				case 'Reference number:' { $line->setRefID($value) }
				case 'Text:' { $line->setDescription($value) }
				case 'Amount:' { $line->setAmount($value) }
				case 'Date:' { $line->setTransactionDate($self->_formatDate($value)) }
				case 'Value date:' { $line->setProcessedDate($self->_formatDate($value)) }
				case 'Currency traded:' {$line->setFXCCY($value) }
				case 'Exchange rate:' { $value =~ s/ //g; $line->setFXRate($value) }
				case 'Amount in foreign currency:' { $value =~ s/ //g; $line->setFXAmount($value) }
			}
	#	}
	}
	#print 'Saving ',$line->toString,"\n";
	#if (defined $line->getRefID() and ! $line->getRefID() eq '')
	#{
#		$self->numbers_store()->addRawExpense($line->toString,$self->account_id());
#	}
#	unlink $filename or warn "could not delete $filename\n";
#	close ($file);
	return $line;
}

#sub readDirectory 
#{
#	my ($self) = @_;
#	my $dir;
#	opendir ($dir, $self->getDirectory) or die "Cannot open ",$self->getDirectory,"\n";
#	my @files = readdir $dir;
#	foreach (@files)
#	{
#		$self->proccessFile($_) if ($_ eq $self->file_name);
#	}
#	closedir $dir;
#}

sub _formatDate
{
	my ($self, $date) = @_;
	$date =~ m/([0-9]{2}).([0-9]{2}).([0-9]{4})/;
	return "$3-$2-$1";
}

###############################################################################
## All functions below for navigation of website ##############################
###############################################################################

sub _pullOnlineData
{
	my $self = shift;
	my @result;

    my $agent = WWW::Mechanize::Firefox->new( tab => 'current', );
    $agent->get('https://www.danskebank.dk/en-dk/Personal/Pages/personal.aspx?secsystem=J2');

    ## setup user id
    $self->_setAllValues($agent, '/html/body/div[3]/div[2]/div/form/fieldset/input', $self->getUserName);
    $self->_setAllValues($agent, '/html/body/div[3]/div[2]/div/form/fieldset/div/div/input', $self->getPassword);
    $agent->xpath('/html/body/div[3]/div[2]/div/form/div/button[1]', one=>1)->click;

    ## deal with nemid code..
    print $agent->xpath('/html/body/div[3]/div[2]/div/div/form/fieldset/label', one=>1)->{textContent};
    $self->_setAllValues($agent, '/html/body/div[3]/div[2]/div/div/form/fieldset/input', '');
    $agent->xpath('/html/body/div[3]/div[2]/div/div/form/div[8]/button[1]', one=>1)->click;

    #$agent->follow_link(text => 'Danske Konto');
    $agent->follow_link(text => $self->getAccountName);

    foreach ($agent->xpath('/html/body/form/div[4]/div[3]/div/div/div[1]/div[3]/div[4]/div[1]/table/tbody/tr'))
    {
        # if should process
    
        # follow link
    
        # process
		my $line = $self->_processFile($agent->xpath('/html/body/div/form/table[2]', one=>1)->{innerHTML});
		push (@result, $line->toString());

        # back
        $agent->back();
    }

	return \@result;

}

sub _setAllValues
{
    my ($self, $agent, $xpath, $value) = @_;
    foreach ($agent->xpath($xpath))
    {
        $_->{value} = $value;
    }
}

1;
