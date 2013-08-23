use strict;
use HTML::Template;

sub template {
    my ($file_name, $param) = @_;
    my $template = HTML::Template->new(filename => "/etc/familytree/template/$file_name.tmpl", die_on_bad_params => 0);
    $template->param($param) if $param;
    print $template->output;
}

1;

