#!/usr/bin/perl -w
# written by andrewt@cse.unsw.edu.au October 2013
# as a starting point for COMP2041 assignment 2
# http://www.cse.unsw.edu.au/~cs2041/assignments/mekong/
# NEED TO FIX: all urls that refer to other pages using hwav057

use CGI qw/:all/;
use HTML::Template;

$debug = 0;
$| = 1;

if (!@ARGV) {
	# run as a CGI script
	cgi_main();
	
} else {
	# for debugging purposes run from the command line
	console_main();
}
exit 0;

# This is very simple CGI code that goes straight
# to the search screen and it doesn't format the
# search results at all

# This is very simple CGI code that goes straight
# to the search screen and it doesn't format the
# search results at all

sub cgi_main {
	set_global_variables();
	read_books($books_file);
    my $action = param('action') || 'signin';
	my $login = param('login') || '';
    my $password = param('password') || '';
	my $search_terms = param('search_terms');
	my $create_new = param('Create New Account');
    my $add_to_basket = param('add_to_basket');
    our %template_variables = (
	    CGI_PARAMS => join(",", map({"$_='".param($_)."'"} param())),
		HIDDEN_VARS => "<input type=\"hidden\" name=\"login\" value=\"$login\">\n<input type=\"hidden\" name=\"password\" value=\"$password\">",
        USER => "$login",
		PASSWORD => "$password",
        PATH_TO_SITE => CGI->new->url(), 
        SIGNING => "Sign In"
	);
    if (authenticate($login,$password)) {
        $template_variables{SIGNING} = "You are signed in as $login. Sign Out.";
        $template_variables{SIGNOUT} = "action=Signout";
    }
    #if (param_used($login)) { $template_variables{USER} = $login; }
	#if (param_used($password)) { $template_variables{PASSWORD} = $password; }
	our $page = "login";
	if ($action eq "Signout") {
        $page = "error";
        $template_variables{ERRORS} = "Congratulations, you have been signed out.";
    } elsif (param_used(param('remove'))) {
        handle_delete_basket();
    } elsif ($action eq "reset_pass") {
        handle_reset_pass();
    } elsif ($action eq "Forgot Password") {
        handle_forgot_password();
    } elsif ($action eq "Checkedout") {
        handle_checkedout();
    } elsif ($action eq "Check Orders") {
        handle_check_orders();
    } elsif ($action eq "View") {
        handle_view_more();
    } elsif ($action eq "Checkout") {
        handle_checkout();
    } elsif (param_used($add_to_basket)) {
        handle_add_to_basket();
	} elsif ($action eq "Basket") {
        handle_view_basket();
    } elsif ($action eq "Create New Account") {
        handle_create_new();
	} elsif ($action eq "confirm") {
        handle_confirm();
    } elsif (param_used($search_terms)) {
        handle_simple_search($search_terms);
	} elsif ($action eq "Authenticate") {
        handle_authenticate();
    } elsif ($action eq "Search") {
        $page = "search";
    }
	# load HTML template from file
	my $template = HTML::Template->new(filename => "design/$page.template", die_on_bad_params => 0);

	# fill in template variables
	$template->param(%template_variables);
	print $template->output;
}

# handles the deleting x amount of books from basket
sub handle_delete_basket {
    my $login = param('login') || "";
    my $remove = param('remove') || "";
    my $amt = param('quantity');
    delete_basket($login,$remove,$amt);
    $page = "error";
    $template_variables{ERRORS} = "Quantity successfully adjusted to $amt.\n";    
}

# handles all steps involved in resetting password
sub handle_reset_pass {
    $page = "error";
    if (param_used(param('new_pass'))) {
        if (legal_password(param('new_pass'))) {
            my $id = handle_reset(param('id'));
            chomp $id;
            my $user = param('login');
            our $last_error = "Change not permitted";
            if (($user eq $id)&&(change_pass(param('login'),param('new_pass')))) {
                $template_variables{ERRORS} = "Congratulations, your password has been changed.";
                remove_first_ocurrence($id, "users/forgot");
            } else {
                $template_variables{ERRORS} = "$last_error<p>Change was not successful.";
            }
        } else {
            $template_variables{ERRORS} = $last_error;
        }
    } else {
        my $user = handle_reset(param('id'));
        chomp $user;
        my $id = param('id');
        if ($user ne "No") {
            $page = "forgot_pass";
            chomp $user;
            $template_variables{PROMPT} = "Enter your new password";
            $template_variables{VARIABLE} = "new_pass";
            $template_variables{VALUE} = "reset_pass";
            $template_variables{KEEP_PARAMS} = "<input type=\"hidden\" name=\"login\" value=\"$user\"><input type=\"hidden\" name=\"id\" value=\"$id\">";
        } else {
            $template_variables{ERRORS} = "Need to provide valid id.";
        }
    }
}

# handles all steps involved in submitting username when forget password
sub handle_forgot_password {
    my $login = param('login') || "";
    if (param_used($login)) {
        $page = "error";
        if (handle_forgot_pass($login)) {
            $template_variables{ERRORS} = "A link to reset your password has been sent to your email.";
        } else { 
            $template_variables{ERRORS} = $last_error;
        }
    } else {
        $page = "forgot_pass";
        $template_variables{PROMPT} = "Enter Username";
        $template_variables{VARIABLE} = "login";
        $template_variables{VALUE} = "Forgot Password";
    }
}

# handles checking the users CC number and CC expiry and then makes order
sub handle_checkedout {
    my $login = param('login');
    if ((legal_credit_card_number(param('CCnum')))&&(legal_expiry_date(param('CCexp')))) {
        finalize_order($login,param('CCnum'),param('CCexp'));
        $page = "error";
        $template_variables{ERRORS} = "Congrats! Your order is now being processed.\n";  
    } else {
        $page = "error";
        $template_variables{ERRORS} = $last_error;
    }
}

# generates html containing all of the users past orders
sub handle_check_orders {
    my $login = param('login');
    my $password = param('password');
    if (authenticate($login,$password)) {
        my $orders;
        my @tmp;
        foreach $or (login_to_orders($login)) {
            @tmp = read_order($or);
            $template_variables{ORDERS} .= "<div class=container>" . format_order(@tmp). "</div><hr>";
        }
        $template_variables{HIDDEN_VARS} .= "<input type=\"hidden\" name=\"action\" value=\"View Order\">"; 
        $page = "orders"; 
    } else {
        $template_variables{ERRORS} = "Error: You need to be logged in to view your previous orders\n";
        $page = "error"; 
    }
}

# generates page for a specific book
sub handle_view_more {
    my $book = param('book');
    $page = "book_info";
    our %book_details;
    $template_variables{ISBN} = $book;  
    $template_variables{IMG_SOURCE} = $book_details{$book}{largeimageurl} || "";
	$template_variables{BOOK_NAME} = $book_details{$book}{title} || "";
    $template_variables{BOOK_INFO} = $book_details{$book}{productdescription} || "";
	$template_variables{AUTHOR} = $book_details{$book}{authors} || "";
	$template_variables{PRICE} = $book_details{$book}{price} || "";
	
	#setting more details column
	$template_variables{PUBLISHER} = $book_details{$book}{publisher} || "";
	$template_variables{EDITION} = $book_details{$book}{edition} || "";
	$template_variables{BINDING} = $book_details{$book}{binding} || "";
	$template_variables{CATALOG} = $book_details{$book}{catalog} || "";
	$template_variables{NUMPAGES} = $book_details{$book}{numpages} || "";
	$template_variables{PUB_DATE} = $book_details{$book}{publication_date} || "";
	$template_variables{EAN} = $book_details{$book}{ean} || "";
	$template_variables{SALESRANK} = $book_details{$book}{salesrank} || "";
	$template_variables{YEAR} = $book_details{$book}{year} || "";
}

# handles entry of data during checkout phase
sub handle_checkout {
    my $login = param('login');
    my $password = param('password');
    $page = "error";
    if (authenticate($login,$password)) {
        my @basket_isbns = read_basket($login);
        if (!@basket_isbns) {
            $template_variables{BASKET} = "Your shopping basket is empty.\n";  
        } else {
            $template_variables{BASKET} = get_book_descriptions(@basket_isbns);
            $template_variables{BASKET} =~ s/Buy Me!/Adjust/g;
            $template_variables{BASKET} =~ s/name\=\"add\_to\_basket\"/name\=\"remove\"/g;
            $template_variables{BASKET} =~ s/<b>Price/<b>Adjust Quantity/;
            my $amt_books = total_books(@basket_isbns);
            $template_variables{AMT_BOOKS} = "Total Price: $amt_books UD\n";
        }
        $page = "checkout";
    } else {
        $template_variables{ERRORS} = "Error: You need to be logged in to check your basket\n";
    }
}

# adds book to basket
sub handle_add_to_basket {
    my $login = param('login');
    my $password = param('password');
    $page = "error";
    if (authenticate($login,$password)) {
        our %book_details;
        my $add_to_basket = param('add_to_basket');
        my $amt = param('quantity');
        my $book = $book_details{$add_to_basket}{title};
        add_basket($login, $add_to_basket, $amt);
        $template_variables{ERRORS} = "Congratulations, $book has been added to your basket.\n";
    } else {
        $template_variables{ERRORS} = "Not logged in, please log in";
    }
}

# shows the current users basket
sub handle_view_basket {
    my $login = param('login') || "";
    my $password = param('password') || "";
    if (authenticate($login,$password)) {
        my @basket_isbns = read_basket($login);
        if (!@basket_isbns) {
            $template_variables{BASKET} = "Your shopping basket is empty.\n";  
        } else {
            $template_variables{BASKET} = get_book_descriptions(@basket_isbns);
            $template_variables{BASKET} =~ s/Buy Me!/Adjust/g;
            $template_variables{BASKET} =~ s/name\=\"add\_to\_basket\"/name\=\"remove\"/g;
            $template_variables{BASKET} =~ s/<b>Price/<b>Adjust Quantity/;
            my $amt_books = total_books(@basket_isbns);
            $template_variables{AMT_BOOKS} = "Total Price: \$".$amt_books."aud.\n";
        }
        $page = "basket";
    } else {
        $page = "error";
        $template_variables{ERRORS} = "Error: You need to be logged in to check your basket\n";
    }
}

# returns results to search term
sub handle_simple_search {
    $template_variables{SEARCH_TERM} = $_[0];
    $template_variables{RESULT_TABLE} = search_results($_[0]);
    $page = "search_form";
}

# checks an email confirm for when creating an account
sub handle_confirm {
    $page = "error";
    if (param_used(param('id'))) {
        if (confirm_user_creation(param('id'))) {
            $template_variables{ERRORS} = "Congratulations, your account has now been confirmed. You may now login.";
        } else {
            $template_variables{ERRORS} = "Error ocurred when confirming email.";
        }    
    } else {
        $template_variables{ERRORS} = "Error: Need unique ID to confirm user creation.";
    }
}

# handles the form for getting user information when registering
sub handle_create_new {
    if (param_used(param('Name'))) {
        my $user = param('Username');
        $page = "error";
        my $rand = create_rand();
        my @to_pass = ($rand, param('Username'), param('Password'), param('Name'), param('Street'));
        push(@to_pass, (param('City'), param('State'),param('Postcode'),param('Email')));
        if (create_new_user(@to_pass)) {
            send_confirm(param('Email'),$rand);
            $template_variables{ERRORS} = "Please check your email for a confirmation.\n";
        } else {
            $template_variables{ERRORS} = $last_error;
        }
    } else {
        # print page to create new account
        $page = "create_new";
    }
}

# checks input from login screen and returns search screen
sub handle_authenticate {
        my $password = param('password');
        my $login = param('login');
		if (authenticate($login, $password)) { 
			$page = "search";
		} else {
            # need page for error
            $page = "error";
            $template_variables{ERRORS} = "Error: $last_error";
		}	
}

# takes an array of information of an order and returns it in nice html
sub format_order {
    (my @order) = @_;
    my $order_time = shift @order;
    my $last_4_digs = shift @order;
    $last_4_digs =~ s/.{12}/xxxxxxxxxxxx/;
    my $cc_exp = shift @order;
    my $line_to_return = get_order_descriptions(@order);
    $line_to_return .= "<p>Order made at ". convert_time($order_time) . "<p>\n";
    $line_to_return .= "By Credit Card num: $last_4_digs<p>Credit Card Exp: $cc_exp<p>\n"; 
}

# changes the password of a particular user
sub change_pass {
    (my $user, my $new_pass) = @_;
    our $last_error;
    if (legal_login($user)) {
        if (remove_first_ocurrence("password","users/$user")) {
            open F, ">>users/$user" or die;
            print F "password\=$new_pass\n";
            close F;
            return 1;
        } else {
            $last_error = "System error";
            return 0;
        }
    } else {
        $last_error = "Username is not valid";
        return 0;
    }
}

# takes unique id and finds the related user. changes account permissions to full user.
sub confirm_user_creation {
    my $id = $_[0];
    my $dir = 'users/to_confirm';
    return 0 if (!remove_first_ocurrence($id,$dir));
    return 1;
}

# takes unique id and finds the related user
sub handle_reset {
    my $id = $_[0];
    use List::Util 'first';
    open F, "users/forgot" or die;
    my @lines = <F>;
    my $user = first { /$id/ } @lines;
    if (defined $user) {
        $user =~ s/\=.+$//;
        return $user;
    } else { return "NO"; }
}

# removes the line containing first ocurrence of $word in $file
# and returns if it occurred or not
sub remove_first_ocurrence {
    (my $word, my $file) = @_;
    open F, $file or die;
    my @lines = <F>;
    my $to_ret = 0;
    close F;
    open F, ">$file" or die;
    foreach my $line (@lines) {
        if ($line =~ /$word/) {
            $to_ret = 1;
        } else {
            print F $line;
        }
    }
    close F;
    return $to_ret;
}

# creates id for confirming account and sends email
sub send_confirm {
    use Mail::Mailer;

    my $from_address = "mekong";
    my $to_address = $_[0];
    my $subject = "Confirm account creation";
    my $unique_id = $_[1];
    my $body = <<eof;
Please go to $template_variables{PATH_TO_SITE}?action=confirm&id=$unique_id to confirm your account.
eof

    my $mailer = Mail::Mailer->new("sendmail");
    $mailer->open({ 
            From    => $from_address,
            To      => $to_address,
            Subject => $subject,
    }); 
    print $mailer $body;
    $mailer->close();
}

# adds entry to user data to allow for password change
# sends email to user so they can change it 
sub handle_forgot_pass {
    our $last_error;
    if (legal_login($_[0]) && open F, "users/$_[0]") {
        my @lines = <F>;
        close F;
        my $email = '';
        foreach $line (@lines) {
            chomp $line;
            if ($line =~ /^email\=([^\@]+\@.+$)/) { $email = $1; }
        }
        if (!param_used($email)) {
            $last_error = "Email does not exist<p>@lines";
            return 0;
        }
        #open F, ">>users/$_[0]" or die;
        my $unique_id = create_rand();
        #print F "forgot\=$unique_id\n";
        #close F;
        open F, ">>users/forgot" or die;
        print F "$_[0]\=$unique_id\n";
        close F;
        send_forgot_password($email,$unique_id);
        return 1;
    } else {
        $last_error = "User does not exist";
        return 0;
    }
}

# sends a password change form to users email
sub send_forgot_password {
    (my $to_address, my $unique_id) = @_;
    use Mail::Mailer;

    my $from_address = "mekong";
    my $subject = "Reset Password";
    my $body = <<eof;
Please go to $template_variables{PATH_TO_SITE}?action=reset_pass&id=$unique_id to change your password.
eof

    my $mailer = Mail::Mailer->new("sendmail");
    $mailer->open({ 
            From    => $from_address,
            To      => "hwav057\@cse.unsw.edu.au",
            Subject => $subject,
    }); 
    print $mailer $body;
    $mailer->close();
}

# creates a relatively large random number for security purposes
sub create_rand {
    my $range = 900000000000;
    my $offset = 100000000000;
    my $random_number = int(rand($range)) + $offset;
    return $random_number;
}

# checks if param has been defined and isn't just empty
sub param_used {
	return ((defined $_[0])&&($_[0] ne ''));
}

# converts seconds since 1st Jan 1970 to a much more readable format
sub convert_time {
    use POSIX qw(strftime);
    $now_string = strftime "%a %b %e %H:%M:%S %Y", localtime($_[0]);
    return $now_string;
}

# adds new user details to the appropriate directory to retain information
sub create_new_user { 
    (my $id, my $user, my $pass, my $name, my $street, my $city, my $state, my $postcode, my $email) = @_;
	if ((legal_login($user))&&(legal_password($pass))) {
        if (-e "users/$user") {
            our $last_error = "Username already taken. Choose another name.\n";
            return 0;
        } else {
		    open F, ">users/$user";
		    print F "password=$pass\nname=$name\nstreet=$street\ncity=$city\nstate=$state\npostcode=$postcode\nemail=$email\n";
		    close F;
            open F, ">>users/to_confirm";
            print F "$id=$user\n";
            close F;
		    return 1;
        }
	} else {
		return 0;
	}
}

# ascii display of search results
sub search_results {
	my ($search_terms) = @_;
	my @matching_isbns = search_books($search_terms);
	my $descriptions = get_book_descriptions(@matching_isbns);
    return $descriptions;
}

###
### Below here are utility functions
### Most are unused by the code above, but you will 
### need to use these functions (or write your own equivalent functions)
### 
###

# return true if specified string can be used as a login

sub legal_login {
	my ($login) = @_;
	our ($last_error);
    if ($login eq 'to_confirm' || $login eq 'forgot') { 
        $last_error = "login '$login': not legal login."; 
        return 0; }
	if ($login !~ /^[a-zA-Z][a-zA-Z0-9]*$/) {
		$last_error = "Invalid login '$login': logins must start with a letter and contain only letters and digits.";
		return 0;
	}
	if (length $login < 3 || length $login > 8) {
		$last_error = "Invalid login: logins must be 3-8 characters long.";
		return 0;
	}
	return 1;
}

# return true if specified string can be used as a password

sub legal_password {
	my ($password) = @_;
	our ($last_error);
	
	if ($password =~ /\s/) {
		$last_error = "Invalid password: password can not contain white space.";
		return 0;
	}
	if (length $password < 5) {
		$last_error = "Invalid password: passwords must contain at least 5 characters.";
		return 0;
	}
	return 1;
}


# return true if specified string could be an ISBN

sub legal_isbn {
	my ($isbn) = @_;
	our ($last_error);
	
	return 1 if $isbn =~ /^\d{9}(\d|X)$/;
	$last_error = "Invalid isbn '$isbn' : an isbn must be exactly 10 digits.";
	return 0;
}


# return true if specified string could be an credit card number

sub legal_credit_card_number {
	my ($number) = @_;
	our ($last_error);
	
	return 1 if $number =~ /^\d{16}$/;
	$last_error = "Invalid credit card number - must be 16 digits.\n";
	return 0;
}

# return true if specified string could be an credit card expiry date

sub legal_expiry_date {
	my ($expiry_date) = @_;
	our ($last_error);
	
	return 1 if $expiry_date =~ /^\d\d\/\d\d$/;
	$last_error = "Invalid expiry date - must be mm/yy, e.g. 11/04.\n";
	return 0;
}



# return total cost of specified books

sub total_books {
	my @isbns = @_;
	our %book_details;
	$total = 0;
	foreach $isbn (@isbns) {
        ($isbn, my $amt) = split /,/,$isbn;
		die "Internal error: unknown isbn $isbn  in total_books" if !$book_details{$isbn}; # shouldn't happen
		my $price = $book_details{$isbn}{price};
		$price =~ s/[^0-9\.]//g;
        $price *= $amt;
		$total += $price;
	}
	return $total;
}

# return true if specified login & password are correct
# user's details are stored in hash user_details

sub authenticate {
	my ($login, $password) = @_;
	our (%user_details, $last_error);
	
	return 0 if !legal_login($login);

    open F, "users/to_confirm" or die;
    my @logins = <F>;
    close F;
    if (grep /$login/, @logins) { 
        $last_error = "User '$login' is not yet confirmed";
        return 0;
    }
    	
	if (!open(USER, "$users_dir/$login")) {
		$last_error = "User '$login' does not exist.";
		return 0;
	}
	my %details =();
	while (<USER>) {
		next if !/^([^=]+)=(.*)/;
        if (/^id\=.*/) {
            $last_error = "User '$login' has not been confirmed yet. Please check your email.";
            return 0;
        }
		$details{$1} = $2;
	}
	close(USER);
	foreach $field (qw(name street city state postcode password)) {
		if (!defined $details{$field}) {
			$last_error = "Incomplete user file: field $field missing";
			return 0;
		}
	}
	if ($details{"password"} ne $password) {
		$last_error = "Incorrect password.";
		return 0;
	 }
	 %user_details = %details;
	 return 1;
}

# read contents of files in the books dir into the hash book
# a list of field names in the order specified in the file
 
sub read_books {
	my ($books_file) = @_;
	our %book_details;
	print STDERR "read_books($books_file)\n" if $debug;
	open BOOKS, $books_file or die "Can not open books file '$books_file'\n";
	my $isbn;
	while (<BOOKS>) {
		if (/^\s*"(\d+X?)"\s*:\s*{\s*$/) {
			$isbn = $1;
			next;
		}
		next if !$isbn;
		my ($field, $value);
		if (($field, $value) = /^\s*"([^"]+)"\s*:\s*"(.*)",?\s*$/) {
			$attribute_names{$field}++;
			print STDERR "$isbn $field-> $value\n" if $debug > 1;
			$value =~ s/([^\\]|^)\\"/$1"/g;
			$book_details{$isbn}{$field} = $value;
		} elsif (($field) = /^\s*"([^"]+)"\s*:\s*\[\s*$/) {
			$attribute_names{$1}++;
			my @a = ();
			while (<BOOKS>) {
				last if /^\s*\]\s*,?\s*$/;
				push @a, $1 if /^\s*"(.*)"\s*,?\s*$/;
			}
			$value = join("\n", @a);
			$value =~ s/([^\\]|^)\\"/$1"/g;
			$book_details{$isbn}{$field} = $value;
			print STDERR "book{$isbn}{$field}=@a\n" if $debug > 1;
		}
	}
	close BOOKS;
}

# return books matching search string

sub search_books {
	my ($search_string) = @_;
	$search_string =~ s/\s*$//;
	$search_string =~ s/^\s*//;
	return search_books1(split /\s+/, $search_string);
}

# return books matching search terms

sub search_books1 {
	my (@search_terms) = @_;
	our %book_details;
	print STDERR "search_books1(@search_terms)\n" if $debug;
	my @unknown_fields = ();
	foreach $search_term (@search_terms) {
		push @unknown_fields, "'$1'" if $search_term =~ /([^:]+):/ && !$attribute_names{$1};
	}
	printf STDERR "$0: warning unknown field%s: @unknown_fields\n", (@unknown_fields > 1 ? 's' : '') if @unknown_fields;
	my @matches = ();
	BOOK: foreach $isbn (sort keys %book_details) {
		my $n_matches = 0;
		if (!$book_details{$isbn}{'=default_search='}) {
			$book_details{$isbn}{'=default_search='} = ($book_details{$isbn}{title} || '')."\n".($book_details{$isbn}{authors} || '');
			print STDERR "$isbn default_search -> '".$book_details{$isbn}{'=default_search='}."'\n" if $debug;
		}
		print STDERR "search_terms=@search_terms\n" if $debug > 1;
		foreach $search_term (@search_terms) {
			my $search_type = "=default_search=";
			my $term = $search_term;
			if ($search_term =~ /([^:]+):(.*)/) {
				$search_type = $1;
				$term = $2;
			}
			print STDERR "term=$term\n" if $debug > 1;
			while ($term =~ s/<([^">]*)"[^"]*"([^>]*)>/<$1 $2>/g) {}
			$term =~ s/<[^>]+>/ /g;
			next if $term !~ /\w/;
			$term =~ s/^\W+//g;
			$term =~ s/\W+$//g;
			$term =~ s/[^\w\n]+/\\b +\\b/g;
			$term =~ s/^/\\b/g;
			$term =~ s/$/\\b/g;
			next BOOK if !defined $book_details{$isbn}{$search_type};
			print STDERR "search_type=$search_type term=$term book=$book_details{$isbn}{$search_type}\n" if $debug;
			my $match;
			eval {
				my $field = $book_details{$isbn}{$search_type};
				# remove text that looks like HTML tags (not perfect)
				while ($field =~ s/<([^">]*)"[^"]*"([^>]*)>/<$1 $2>/g) {}
				$field =~ s/<[^>]+>/ /g;
				$field =~ s/[^\w\n]+/ /g;
				$match = $field !~ /$term/i;
			};
			if ($@) {
				$last_error = $@;
				$last_error =~ s/;.*//;
				return (); 
			}
			next BOOK if $match;
			$n_matches++;
		}
		push @matches, $isbn if $n_matches > 0;
	}
	
	sub bySalesRank {
		my $max_sales_rank = 100000000;
		my $s1 = $book_details{$a}{SalesRank} || $max_sales_rank;
		my $s2 = $book_details{$b}{SalesRank} || $max_sales_rank;
		return $a cmp $b if $s1 == $s2;
		return $s1 <=> $s2;
	}
	
	return sort bySalesRank @matches;
}


# return books in specified user's basket

sub read_basket {
	my ($login) = @_;
	our %book_details;
	open F, "$baskets_dir/$login" or return ();
	my @isbns = <F>;

	close(F);
	chomp(@isbns);
	#!$book_details{$_} && die "Internal error: unknown isbn $_ in basket\n" foreach @isbns;
	return @isbns;
}


# delete specified book from specified user's basket
# only first occurance is deleted

sub delete_basket {
	(my $login, my $delete_isbn, my $amt_remove) = @_;
	my @isbns = read_basket($login);
	open F, ">$baskets_dir/$login" or die "Can not open $baskets_dir/$login: $!";
	foreach $isbn (@isbns) {
		if ($isbn =~ /$delete_isbn/) {
            if ($amt_remove > 0) {
                $isbn =~ s/,\d+/,$amt_remove/;
            } else {
                $delete_isbn = "";
                next;
            }
		}
		print F "$isbn\n";
	}
	close(F);
	unlink "$baskets_dir/$login" if ! -s "$baskets_dir/$login";
}


# add specified book to specified user's basket

sub add_basket {
	my ($login, $isbn, $amt) = @_;
    my @basket;
	if (open F, "$baskets_dir/$login") { # or die "Can not open $baskets_dir/$login::$! \n";
        @basket = <F>;
        close F;
    }
    open F, ">$baskets_dir/$login" or die;
    my $flag = 0;
    foreach my $item (@basket) {
        chomp $item;
        if ($item =~ /^$isbn,(\d+)$/) {
            $amt += $1;
            $item = "$isbn,$amt";
            $flag = 1;
        } 
        print F "$item\n";
    }
    print F "$isbn,$amt\n" if $flag == 0;
	close(F);
}


# finalize specified order

sub finalize_order {
	my ($login, $credit_card_number, $expiry_date) = @_;
	my $order_number = 0;

	if (open ORDER_NUMBER, "$orders_dir/NEXT_ORDER_NUMBER") {
		$order_number = <ORDER_NUMBER>;
		chomp $order_number;
		close(ORDER_NUMBER);
	}
	$order_number++ while -r "$orders_dir/$order_number";
	open F, ">$orders_dir/NEXT_ORDER_NUMBER" or die "Can not open $orders_dir/NEXT_ORDER_NUMBER: $!\n";
	print F ($order_number + 1);
	close(F);

	my @basket_isbns = read_basket($login);
	open ORDER,">$orders_dir/$order_number" or die "Can not open $orders_dir/$order_number:$! \n";
	print ORDER "order_time=".time()."\n";
	print ORDER "credit_card_number=$credit_card_number\n";
	print ORDER "expiry_date=$expiry_date\n";
	print ORDER join("\n",@basket_isbns)."\n";
	close(ORDER);
	unlink "$baskets_dir/$login";
	
	open F, ">>$orders_dir/$login" or die "Can not open $orders_dir/$login:$! \n";
	print F "$order_number\n";
	close(F);
	
}


# return order numbers for specified login

sub login_to_orders {
	my ($login) = @_;
	open F, "$orders_dir/$login" or return ();
	@order_numbers = <F>;
	close(F);
	chomp(@order_numbers);
	return @order_numbers;
}



# return contents of specified order

sub read_order {
	my ($order_number) = @_;
	open F, "$orders_dir/$order_number" or warn "Can not open $orders_dir/$order_number:$! \n";
	@lines = <F>;
	close(F);
	chomp @lines;
	foreach (@lines[0..2]) {s/.*=//};
	return @lines;
}

###
### functions below are only for testing from the command line
### Your do not need to use these funtions
###

sub console_main {
	set_global_variables();
	$debug = 1;
	foreach $dir ($orders_dir,$baskets_dir,$users_dir) {
		if (! -d $dir) {
			print "Creating $dir\n";
			mkdir($dir, 0777) or die("Can not create $dir: $!");
		}
	}
	read_books($books_file);
	my @commands = qw(login new_account search details add drop basket checkout orders quit);
	my @commands_without_arguments = qw(basket checkout orders quit);
	my $login = "";
	
	print "mekong.com.au - ASCII interface\n";
	while (1) {
		$last_error = "";
		print "> ";
		$line = <STDIN> || last;
		$line =~ s/^\s*>\s*//;
		$line =~ /^\s*(\S+)\s*(.*)/ || next;
		($command, $argument) = ($1, $2);
		$command =~ tr/A-Z/a-z/;
		$argument = "" if !defined $argument;
		$argument =~ s/\s*$//;
		
		if (
			$command !~ /^[a-z_]+$/ ||
			!grep(/^$command$/, @commands) ||
			grep(/^$command$/, @commands_without_arguments) != ($argument eq "") ||
			($argument =~ /\s/ && $command ne "search")
		) {
			chomp $line;
			$line =~ s/\s*$//;
			$line =~ s/^\s*//;
			incorrect_command_message("$line");
			next;
		}

		if ($command eq "quit") {
			print "Thanks for shopping at mekong.com.au.\n";
			last;
		}
		if ($command eq "login") {
			$login = login_command($argument);
			next;
		} elsif ($command eq "new_account") {
			$login = new_account_command($argument);
			next;
		} elsif ($command eq "search") {
			search_command($argument);
			next;
		} elsif ($command eq "details") {
			details_command($argument);
			next;
		}
		
		if (!$login) {
			print "Not logged in.\n";
			next;
		}
		
		if ($command eq "basket") {
			basket_command($login);
		} elsif ($command eq "add") {
			add_command($login, $argument);
		} elsif ($command eq "drop") {
			drop_command($login, $argument);
		} elsif ($command eq "checkout") {
			checkout_command($login);
		} elsif ($command eq "orders") {
			orders_command($login);
		} else {
			warn "internal error: unexpected command $command";
		}
	}
}

sub login_command {
	my ($login) = @_;
	if (!legal_login($login)) {
		print "$last_error\n";
		return "";
	}
	if (!-r "$users_dir/$login") {
		print "User '$login' does not exist.\n";
		return "";
	}
	printf "Enter password: ";
	my $pass = <STDIN>;
	chomp $pass;
	if (!authenticate($login, $pass)) {
		print "$last_error\n";
		return "";
	}
	$login = $login;
	print "Welcome to mekong.com.au, $login.\n";
	return $login;
}

sub new_account_command {
	my ($login) = @_;
	if (!legal_login($login)) {
		print "$last_error\n";
		return "";
	}
	if (-r "$users_dir/$login") {
		print "Invalid user name: login already exists.\n";
		return "";
	}
	if (!open(USER, ">$users_dir/$login")) {
		print "Can not create user file $users_dir/$login: $!";
		return "";
	}
	foreach $description (@new_account_rows) {
		my ($name, $label)  = split /\|/, $description;
		next if $name eq "login";
		my $value;
		while (1) {
			print "$label ";
			$value = <STDIN>;
			exit 1 if !$value;
			chomp $value;
			if ($name eq "password" && !legal_password($value)) {
				print "$last_error\n";
				next;
			}
			last if $value =~ /\S+/;
		}
		$user_details{$name} = $value;
		print USER "$name=$value\n";
	}
	close(USER);
	print "Welcome to mekong.com.au, $login.\n";
	return $login;
}

sub search_command {
	my ($search_string) = @_;
	$search_string =~ s/\s*$//;
	$search_string =~ s/^\s*//;
	search_command1(split /\s+/, $search_string);
}

sub search_command1 {
	my (@search_terms) = @_;
	my @matching_isbns = search_books1(@search_terms);
	if ($last_error) {
		print "$last_error\n";
	} elsif (@matching_isbns) {
		print_books(@matching_isbns);
	} else {
		print "No books matched.\n";
	}
}

sub details_command {
	my ($isbn) = @_;
	our %book_details;
	if (!legal_isbn($isbn)) {
		print "$last_error\n";
		return;
	}
	if (!$book_details{$isbn}) {
		print "Unknown isbn: $isbn.\n";
		return;
	}
	print_books($isbn);
	foreach $attribute (sort keys %{$book_details{$isbn}}) {
		next if $attribute =~ /Image|=|^(|price|title|authors|productdescription)$/;
		print "$attribute: $book_details{$isbn}{$attribute}\n";
	}
	my $description = $book_details{$isbn}{productdescription} or return;
	$description =~ s/\s+/ /g;
	$description =~ s/\s*<p>\s*/\n\n/ig;
	while ($description =~ s/<([^">]*)"[^"]*"([^>]*)>/<$1 $2>/g) {}
	$description =~ s/(\s*)<[^>]+>(\s*)/$1 $2/g;
	$description =~ s/^\s*//g;
	$description =~ s/\s*$//g;
	print "$description\n";
}

sub basket_command {
	my ($login) = @_;
	my @basket_isbns = read_basket($login);
	if (!@basket_isbns) {
		print "Your shopping basket is empty.\n";
	} else {
		print_books(@basket_isbns);
		printf "Total: %11s\n", sprintf("\$%.2f", total_books(@basket_isbns));
	}
}

sub add_command {
	my ($login,$isbn) = @_;
	our %book_details;
	if (!legal_isbn($isbn)) {
		print "$last_error\n";
		return;
	}
	if (!$book_details{$isbn}) {
		print "Unknown isbn: $isbn.\n";
		return;
	}
	add_basket($login, $isbn);
}

sub drop_command {
	my ($login,$isbn) = @_;
	my @basket_isbns = read_basket($login);
	if (!legal_isbn($argument)) {
		print "$last_error\n";
		return;
	}
	if (!grep(/^$isbn$/, @basket_isbns)) {
		print "Isbn $isbn not in shopping basket.\n";
		return;
	}
	delete_basket($login, $isbn);
}

sub checkout_command {
	my ($login) = @_;
	my @basket_isbns = read_basket($login);
	if (!@basket_isbns) {
		print "Your shopping basket is empty.\n";
		return;
	}
	print "Shipping Details:\n$user_details{name}\n$user_details{street}\n$user_details{city}\n$user_details{state}, $user_details{postcode}\n\n";
	print_books(@basket_isbns);
	printf "Total: %11s\n", sprintf("\$%.2f", total_books(@basket_isbns));
	print "\n";
	my ($credit_card_number, $expiry_date);
	while (1) {
			print "Credit Card Number: ";
			$credit_card_number = <>;
			exit 1 if !$credit_card_number;
			$credit_card_number =~ s/\s//g;
			next if !$credit_card_number;
			last if $credit_card_number =~ /^\d{16}$/;
			last if legal_credit_card_number($credit_card_number);
			print "$last_error\n";
	}
	while (1) {
			print "Expiry date (mm/yy): ";
			$expiry_date = <>;
			exit 1 if !$expiry_date;
			$expiry_date =~ s/\s//g;
			next if !$expiry_date;
			last if legal_expiry_date($expiry_date);
			print "$last_error\n";
	}
	finalize_order($login, $credit_card_number, $expiry_date);
}

sub orders_command {
	my ($login) = @_;
	print "\n";
	foreach $order (login_to_orders($login)) {
		my ($order_time, $credit_card_number, $expiry_date, @isbns) = read_order($order);
		$order_time = localtime($order_time);
		print "Order #$order - $order_time\n";
		print "Credit Card Number: $credit_card_number (Expiry $expiry_date)\n";
		print_books(@isbns);
		print "\n";
	}
}

# print descriptions of specified books
sub print_books(@) {
	my @isbns = @_;
	return get_book_descriptions(@isbns);
}

# return book descriptions for basket
sub get_book_basket {
	if (!defined @_) { return "\n"; } 
	my @isbns = @_;
	my $descriptions = <<eof;
<form class="btn-group" method="get" align="center">
$template_variables{HIDDEN_VARS} 
<table class="table" align="center">
<thead>
<td><b>Image</td>
<td><b>Description</td>
<td><b>Price</td>
</thead>
<tbody>
eof
	our %book_details;
	foreach $isbn (@isbns) {
		die "Internal error: unknown isbn $isbn in print_books\n" if !$book_details{$isbn}; # shouldn't happen
		my $title = $book_details{$isbn}{title} || "";
		my $authors = $book_details{$isbn}{authors} || "";
		my $image = $book_details{$isbn}{smallimageurl} || "";
		my $big_image = $book_details{$isbn}{largeimageurl} || "";
		$authors =~ s/\n([^\n]*)$/ & $1/g;
		$authors =~ s/\n/, /g;
		$descriptions .= <<eof;
<tr><td><a href="$big_image" ><img src="$image" ></a></td> 
<td><i>$title</i><br>$authors<br></td><td>
<button type="submit" class="btn btn-default" name="add_to_basket" value="$isbn">Buy Me!</button> 
<br><br>$book_details{$isbn}{price}</td></tr>
eof
		#$descriptions .= start_form,submit("$isbn",'Buy Me!'),end_form;
	}
	$descriptions .= "</tbody></table></form>";
	return $descriptions;
}

# this returns a info page about the book. note that it is full page
sub get_full_info {
	if (!defined @_) { return "\n"; } 
	my @isbns = @_;
	my $descriptions = <<eof;
<form class="btn-group" method="get">
$template_variables{HIDDEN_VARS} 
<table class="table">
<thead>
<td><b>Image</td>
<td><b>Description</td>
<td><b>Price</td>
</thead>
<tbody>
eof
	our %book_details;
	foreach $isbn (@isbns) {
		die "Internal error: unknown isbn $isbn in print_books\n" if !$book_details{$isbn}; # shouldn't happen
		my $title = $book_details{$isbn}{title} || "";
		my $authors = $book_details{$isbn}{authors} || "";
		my $image = $book_details{$isbn}{smallimageurl} || "";
		my $big_image = $book_details{$isbn}{largeimageurl} || "";
		$authors =~ s/\n([^\n]*)$/ & $1/g;
		$authors =~ s/\n/, /g;
		$descriptions .= <<eof;
<tr><td><a href="$big_image" ><img src="$image" ></a></td> 
<td><i>$title</i><br>$authors <i><a href=$template_variables{PATH_TO_SITE}?action=View&book=$isbn>more</a></i><br></td><td>
<button type="submit" class="btn btn-default" name="add_to_basket" value="$isbn">Buy Me!</button> 
<br><br>$book_details{$isbn}{price}</td></tr>
eof
		#$descriptions .= start_form,submit("$isbn",'Buy Me!'),end_form;
	}
	$descriptions .= "</tbody></table></form>";
	return $descriptions;
}

# return order descriptions of specified books in formatted table html
sub get_order_descriptions {
	if (!defined @_) { return "\n"; } 
	my @isbns = @_;
	my $descriptions = <<eof;
<form class="btn-group" method="get">
$template_variables{HIDDEN_VARS} 
<table class="table" width="100%">
<thead>
<td style="width:150px"><b>Image</td>
<td style="width:600px"><b>Description</td>
<td style="width:150px"><b>Quantity Ordered</td>
<td style="width:150px"><b>Price</td>
</thead>
<tbody>
eof
	our %book_details;
    my $amt;
	foreach $isbn (@isbns) {
        ($isbn,$amt) = split /,/,$isbn; 
		die "Internal error: unknown isbn $isbn in print_books\n" if !$book_details{$isbn}; # shouldn't happen
		my $title = $book_details{$isbn}{title} || "";
		my $authors = $book_details{$isbn}{authors} || "";
		my $image = $book_details{$isbn}{smallimageurl} || "";
		my $big_image = $book_details{$isbn}{largeimageurl} || "";
        my $price = $book_details{$isbn}{price} || "";
        $price =~ s/\$//;
        $price *= $amt;
		$authors =~ s/\n([^\n]*)$/ & $1/g;
		$authors =~ s/\n/, /g;
		$descriptions .= <<eof;
<tr><td><a href="$big_image" ><img src="$image" ></a></td> 
<td><i>$title</i><br>$authors <i><a href=$template_variables{PATH_TO_SITE}?action=View&book=$isbn>more</a></i><br></td>
<td>You purchased: $amt</td>
<td>Price Paid:
<br><br>\$$price</td></tr>
eof
		#$descriptions .= start_form,submit("$isbn",'Buy Me!'),end_form;
	}
	$descriptions .= "</tbody></table></form>";
	return $descriptions;
}

# return descriptions of specified books in formatted table html
sub get_book_descriptions {
	if (!defined @_) { return "\n"; } 
	my @isbns = @_;
	my $descriptions = <<eof;
<table class="table">
<thead>
<td><b>Image</td>
<td><b>Description</td>
<td><b>Amount</td>
<td><b>Price</td>
</thead>
<tbody>
eof
	our %book_details;
	foreach $isbn (@isbns) {
        my $amt = 1;
        if ($isbn =~ /\,/) {
            ($isbn, $amt) = split /,/,$isbn;
        }
		die "Internal error: unknown isbn $isbn in print_books\n" if !$book_details{$isbn}; # shouldn't happen
		my $title = $book_details{$isbn}{title} || "";
		my $authors = $book_details{$isbn}{authors} || "";
		my $image = $book_details{$isbn}{smallimageurl} || "";
		my $big_image = $book_details{$isbn}{largeimageurl} || "";
		$authors =~ s/\n([^\n]*)$/ & $1/g;
		$authors =~ s/\n/, /g;
		$descriptions .= <<eof;
<form class="btn-group" method="get">
$template_variables{HIDDEN_VARS} 
<tr><td><a href="$big_image" ><img src="$image" ></a></td> 
<td><i>$title</i><br>$authors <i><a href=$template_variables{PATH_TO_SITE}?action=View&book=$isbn&login=$template_variables{USER}&password=$template_variables{PASSWORD}>more</a></i><br></td>
<td><input type="text" name="quantity" class="form_control spinedit noSelect" id="spinEdit" value="$amt" min="1"></td>
<td><button type="submit" class="btn btn-default" name="add_to_basket" value="$isbn">Buy Me!</button> 
<br><br>$book_details{$isbn}{price}</td></tr></form>
eof
		#$descriptions .= start_form,submit("$isbn",'Buy Me!'),end_form;
	}
	$descriptions .= "</tbody></table>";
	return $descriptions;
}

sub set_global_variables {
    $base_dir = ".";
    $books_file = "$base_dir/books.json";
    $orders_dir = "$base_dir/orders";
    $baskets_dir = "$base_dir/baskets";
    $users_dir = "$base_dir/users";
    $last_error = "";
    %user_details = ();
    %book_details = ();
    %attribute_names = ();
    @new_account_rows = (
	    'login|Login:|10',
	    'password|Password:|10',
	    'name|Full Name:|50',
	    'street|Street:|50',
	    'city|City/Suburb:|25',
	    'state|State:|25',
	    'postcode|Postcode:|25',
	    'email|Email Address:|35'
	);
}


sub incorrect_command_message {
	my ($command) = @_;
	print "Incorrect command: $command.\n";
	print <<eof;
possible commands are:
login <login-name>
new_account <login-name>                    
search <words>
details <isbn>
add <isbn>
drop <isbn>
basket
checkout
orders
quit
eof
}


