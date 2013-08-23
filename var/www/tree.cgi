#!/usr/bin/perl

use lib "/etc/familytree/lib";
use strict;

use CGI;
use CGI::Carp qw(fatalsToBrowser);

use Database;

my $q  = new CGI;
my $db = new Database;
my ($red, $green, $blue);

print $q->header;

my $member_id = $q->param('member_id');
if ($member_id) {
    my $children = $db->{dbh}->selectall_hashref(qq{
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
        WHERE
            a.parent_id = ?
    }, 'id', undef, $member_id);

    my $number_of_children = scalar %$children;
    if ($number_of_children) {
        my $div_width = int (100 / $number_of_children);

        print qq{<div class="cntnr">};

        for my $child (sort {$a <=> $b} keys %$children) {
            ($red, $green, $blue) = random_color();

            print qq{<div id="div_$child" class="member" style="width: $div_width%; background-color: rgb($red, $green, $blue);" onclick="show_children($child);">$children->{$child}{name}};
            print " & $children->{$child}{spouse}" if $children->{$child}{spouse};
            print "</div>\n";
        }

        print "</div>\n";
    }

    exit;
}

my $top_member = $db->{dbh}->selectrow_hashref(qq{
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
    WHERE
        a.parent_id = 0
});

($red, $green, $blue) = random_color();

print qq{
    <html>
        <head>
            <title>Family Tree</title>
            <script type="text/javascript" src="./js/jquery-1.5.1.min.js"></script>
            <script type="text/javascript">
                var clicked = {};
                function show_children(member_id) {
                    if (!clicked[member_id]) {
                        clicked[member_id] = 1;
                        \$.post('',
                            {'member_id':member_id},
                            function(data) {
                                if (data) {
                                    \$("#div_"+member_id).append(data);
                                }
                            }
                        );
                    }
                }
            </script>
            <style type="text/css">
                div {
                    position: relative;
                    float: left;
                    height: 40px;
                    padding-top: 20px;
                    text-align: center;
                }
                .cntnr {
                    width: 100%;
                }
                .member {
                    min-height: 40px;
                    height: auto !important;
                    cursor: pointer;
                }
            </style>
        </head>
        <body>
            <div id="div_$top_member->{id}" class="cntnr member" style="background-color: rgb($red, $green, $blue);" onclick="show_children($top_member->{id});">$top_member->{name}
};

print " & $top_member->{spouse}" if $top_member->{spouse};

print qq{
            </div>
        </body>
    </html>
};

sub random_color {
    return (int(rand(255)), int(rand(255)), int(rand(255)));
}

