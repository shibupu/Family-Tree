#!/usr/bin/perl

use lib "/etc/familytree/lib";
use strict;

use CGI;
use CGI::Carp qw(fatalsToBrowser);
use HTML::Template;

use Database;

my $q  = new CGI;
my $db = new Database;

my $action = $q->param('action');
my $id     = $q->param('id');

print $q->header;

template('header');

if ($action eq 'add') {
    add_edit('add');
}
elsif ($action eq 'edit') {
    add_edit('edit');
}
elsif ($action) {
    eval "$action()";
    list();
}
else {
    list();
}

template('footer');

sub list {
    my $param = {
        members => $db->{dbh}->selectall_arrayref(qq{
            SELECT
                a.id AS id,
                a.name AS name,
                b.name AS spouse
            FROM
                member a
            LEFT JOIN
                spouse b
            ON
                a.id = b.member_id
        }, { Slice => {} })
    };
    template('members', $param);
}

sub add_edit {
    my $action = shift;
    my ($param, %selected);

    if (($action eq 'edit') && $id) {
        $param = $db->{dbh}->selectrow_hashref(qq{
            SELECT
                a.id AS id,
                a.name AS name,
                a.gender AS gender,
                a.address AS address,
                a.phone AS phone,
                a.mobile AS mobile,
                a.email AS email,
                a.occupation AS occupation,
                a.birth_date AS birth_date,
                a.photo AS photo,
                a.parent_id AS parent_id,
                b.name AS spouse,
                b.address AS spouse_address,
                b.phone AS spouse_phone,
                b.mobile AS spouse_mobile,
                b.email AS spouse_email,
                b.occupation AS spouse_occupation,
                b.birth_date AS spouse_birth_date,
                b.wedding_date AS wedding_date,
                b.photo AS spouse_photo
            FROM
                member a
            LEFT JOIN
                spouse b
            ON
                a.id = b.member_id
            WHERE
                a.id = ?
        }, undef, $id);
        $selected{parent}{$param->{parent_id}} = qq{ selected="selected"};
        $param->{"$param->{gender}_gender_selected"} = qq{ selected="selected"};

        $param->{button} = 'Update';
        $param->{action} = 'update';
    }
    else {
        $param->{button} = 'Add';
        $param->{action} = 'insert';
    }

    $param->{parents} = $db->{dbh}->selectall_arrayref(qq{
        SELECT
            id AS parent_id,
            name AS parent_name
        FROM
            member
    }, { Slice => {} });
    $_->{parent_selected} = $selected{parent}{$_->{parent_id}}
        for @{$param->{parents}};

    template('member', $param);
}

sub insert {
    my $params = $q->Vars;
    my $photo = $q->upload('photo');
    my $spouse_photo = $q->upload('spouse_photo');
    my ($photo_file_name, $spouse_photo_file_name);
    $photo_file_name = get_photo_name($photo) if $photo;
    $spouse_photo_file_name = get_photo_name($spouse_photo) if $spouse_photo;

    my $data = {
        name       => $params->{name},
        gender     => $params->{gender},
        address    => $params->{address},
        phone      => $params->{phone},
        mobile     => $params->{mobile},
        email      => $params->{email},
        occupation => $params->{occupation},
        birth_date => $params->{birth_date},
        photo      => $photo_file_name,
        parent_id  => $params->{parent}
    };

    my $rows = $db->insert('member', $data);
    if ($rows > 0) {
        upload_photo($photo_file_name, $photo) if $photo_file_name;

        if ($params->{spouse}) {
            my ($member_id) = $db->{dbh}->selectrow_array("SELECT LAST_INSERT_ID()");
            $data = {
                name         => $params->{spouse},
                address      => $params->{spouse_address},
                phone        => $params->{spouse_phone},
                mobile       => $params->{spouse_mobile},
                email        => $params->{spouse_email},
                occupation   => $params->{spouse_occupation},
                birth_date   => $params->{spouse_birth_date},
                wedding_date => $params->{wedding_date},
                photo        => $photo_file_name,
                member_id    => $member_id
            };
            $rows = $db->insert('spouse', $data);
            upload_photo($spouse_photo_file_name, $spouse_photo) if $rows > 0 && $spouse_photo_file_name;
        }
    }
}

sub update {
    return if !$id;

    my $params = $q->Vars;
    my $photo = $q->upload('photo');
    my $spouse_photo = $q->upload('spouse_photo');
    my ($photo_file_name, $spouse_photo_file_name, $old_photo, $old_spouse_photo);

    if ($photo) {
        ($old_photo) = $db->{dbh}->selectrow_array(qq{
            SELECT
                photo
            FROM
                member
            WHERE
                id = ?
        }, undef, $id);

        $photo_file_name = get_photo_name($photo);
    }

    if ($spouse_photo) {
        ($old_spouse_photo) = $db->{dbh}->selectrow_array(qq{
            SELECT
                photo
            FROM
                spouse
            WHERE
                member_id = ?
        }, undef, $id);

        $spouse_photo_file_name = get_photo_name($spouse_photo);
    }

    # Update member table
    my $data = {
        name       => $params->{name},
        gender     => $params->{gender},
        address    => $params->{address},
        phone      => $params->{phone},
        mobile     => $params->{mobile},
        email      => $params->{email},
        occupation => $params->{occupation},
        birth_date => $params->{birth_date},
        photo      => $photo_file_name,
        parent_id  => $params->{parent}
    };
    my $cond = { id => $id };

    my $rows = $db->update('member', $data, $cond);
    if ($rows > 0 && $photo_file_name) {
        upload_photo($photo_file_name, $photo);
        delete_photo($old_photo);
    }

    # Try to insert into spouse table.
    # If spouse already exists, it will fail as member_id is unique.
    $data = {
        name         => $params->{spouse},
        address      => $params->{spouse_address},
        phone        => $params->{spouse_phone},
        mobile       => $params->{spouse_mobile},
        email        => $params->{spouse_email},
        occupation   => $params->{spouse_occupation},
        birth_date   => $params->{spouse_birth_date},
        wedding_date => $params->{wedding_date},
        photo        => $spouse_photo_file_name,
        member_id    => $id
    };
    $rows = $db->insert('spouse', $data);

    if ($rows <= 0) {
        # Update spouse table.
        $data = {
            name         => $params->{spouse},
            address      => $params->{spouse_address},
            phone        => $params->{spouse_phone},
            mobile       => $params->{spouse_mobile},
            email        => $params->{spouse_email},
            occupation   => $params->{spouse_occupation},
            birth_date   => $params->{spouse_birth_date},
            wedding_date => $params->{wedding_date},
            photo        => $spouse_photo_file_name
        };
        $cond = { member_id => $id };
        $rows = $db->update('spouse', $data, $cond);
    }

    if ($rows > 0 && $spouse_photo_file_name) {
        upload_photo($spouse_photo_file_name, $spouse_photo);
        delete_photo($old_spouse_photo);
    }
}

sub del {
    return if !$id;

    my ($photo) = $db->{dbh}->selectrow_array(qq{
        SELECT
            photo
        FROM
            member
        WHERE
            id = ?
    }, undef, $id);

    my $rows = $db->delete('member', 'id', $id);
    if ($rows > 0) {
        delete_photo($photo);

        my ($spouse_photo) = $db->{dbh}->selectrow_array(qq{
            SELECT
                photo
            FROM
                spouse
            WHERE
                member_id = ?
        }, undef, $id);

        $rows = $db->delete('spouse', 'member_id', $id);
        delete_photo($spouse_photo) if $rows > 0;
    }
}

sub template {
    my ($file_name, $param) = @_;
    return if !$file_name;
    my $template = HTML::Template->new(filename => "/etc/familytree/template/$file_name.tmpl", die_on_bad_params => 0);
    $template->param($param) if $param;
    print $template->output;
}

sub get_photo_name {
    my $file = shift;
    my @splits = split /\\/, $file;
    my ($file_name, $extension) = split("\\.", $splits[-1]);
    $file_name =~ s/\W//g;
    return $file_name . '_' . time . '.' . $extension;
}

sub upload_photo {
    my ($file_name, $file) = @_;

    open (UPLOADFILE, ">../photo/$file_name") or die $!;
    while (<$file>) {
        print UPLOADFILE;
    }
    close UPLOADFILE;
}

sub delete_photo {
    my $file_name = shift;
    unlink "../photo/$file_name" if $file_name;
}
