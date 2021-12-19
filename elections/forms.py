import json

from django.forms import inlineformset_factory, ModelForm, CharField, Textarea
from django.utils import six
from django.utils.encoding import force_text
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from elections.models import Voter, Nominee, Ballot

class BallotForm(ModelForm):
    nominees = CharField(widget=Textarea, disabled=True, required=False, label="nominees")
    results = CharField(widget=Textarea, disabled=True, required=False, label="raw results",
        help_text="Ranked choice raw result."
    )

    class Meta:
        model = Ballot
        exclude = []

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance', None)
        if instance:
            kwargs.update(initial={
                "nominees": json.dumps(instance.get_nominees(), indent=2),
                "results": json.dumps(instance.get_results(), indent=2),
            })
        super(BallotForm, self).__init__(*args, **kwargs)

class NomineeForm(ModelForm):
    class Meta:
        model = Nominee
        fields=("first_name", "last_name", "email", "ballots")
    
    def __init__(self, *args, **kwargs):
        super(NomineeForm, self).__init__(*args, **kwargs)
        self.label_suffix = ""  # Removes : as label suffix
        # for key in self.fields:
        #     self.fields[key].required = True 

    def _html_output(self, normal_row, checked_row, error_row, row_ender, help_text_html, errors_on_separate_row):
        "Helper function for outputting HTML. Used by as_table(), as_ul(), as_p()."
        # Slightly modified from super to allow our styling with checkbox/radiobutton which we'll use "checked_row"
        top_errors = self.non_field_errors()  # Errors that should be displayed above all fields.
        output, hidden_fields = [], []

        for name, field in self.fields.items():
            html_class_attr = ''
            bf = self[name]
            # Escape and cache in local variable.
            bf_errors = self.error_class([conditional_escape(error) for error in bf.errors])
            if bf.is_hidden:
                if bf_errors:
                    top_errors.extend(
                        [_('(Hidden field %(name)s) %(error)s') % {'name': name, 'error': force_text(e)}
                         for e in bf_errors])
                hidden_fields.append(six.text_type(bf))
            else:
                # Create a 'class="..."' attribute if the row should have any
                # CSS classes applied.
                css_classes = bf.css_classes()
                if css_classes:
                    html_class_attr = ' class="%s"' % css_classes

                if errors_on_separate_row and bf_errors:
                    output.append(error_row % force_text(bf_errors))

                if bf.label:
                    label = conditional_escape(force_text(bf.label))
                    label = bf.label_tag(label) or ''
                else:
                    label = ''

                if field.help_text:
                    help_text = help_text_html % force_text(field.help_text)
                else:
                    help_text = ''

                if field.widget.input_type in ("checkbox", "radio"):
                    row_format = checked_row
                else:
                    row_format = normal_row
                output.append(row_format % {
                    'errors': force_text(bf_errors),
                    'label': force_text(label),
                    'field': six.text_type(bf),
                    'help_text': help_text,
                    'html_class_attr': html_class_attr,
                    'css_classes': css_classes,
                    'field_name': bf.html_name,
                })

        if top_errors:
            output.insert(0, error_row % force_text(top_errors))

        if hidden_fields:  # Insert any hidden fields in the last row.
            str_hidden = ''.join(hidden_fields)
            if output:
                last_row = output[-1]
                # Chop off the trailing row_ender (e.g. '</td></tr>') and
                # insert the hidden fields.
                if not last_row.endswith(row_ender):
                    # This can happen in the as_p() case (and possibly others
                    # that users write): if there are only top errors, we may
                    # not be able to conscript the last row for our purposes,
                    # so insert a new, empty row.
                    last_row = (normal_row % {
                        'errors': '',
                        'label': '',
                        'field': '',
                        'help_text': '',
                        'html_class_attr': html_class_attr,
                        'css_classes': '',
                        'field_name': '',
                    })
                    output.append(last_row)
                output[-1] = last_row[:-len(row_ender)] + str_hidden + row_ender
            else:
                # If there aren't any rows in the output, just append the
                # hidden fields.
                output.append(str_hidden)
        return mark_safe('\n'.join(output))

    def as_table(self):
        "Returns this form rendered as HTML <tr>s -- excluding the <table></table>."
        return self._html_output(
            normal_row='<tr%(html_class_attr)s><th>%(label)s</th><td>%(errors)s%(field)s%(help_text)s</td></tr>',
            checked_row = '<tr%(html_class_attr)s><th></th><td>%(errors)s%(field)s %(label)s%(help_text)s</td></tr>',
            error_row='<tr><td colspan="2">%s</td></tr>',
            row_ender='</td></tr>',
            help_text_html='<br /><span class="helptext">%s</span>',
            errors_on_separate_row=False)

    def as_ul(self):
        "Returns this form rendered as HTML <li>s -- excluding the <ul></ul>."
        return self._html_output(
            normal_row='<li%(html_class_attr)s>%(errors)s%(label)s %(field)s%(help_text)s</li>',
            checked_row='<li%(html_class_attr)s>%(errors)s%(field)s %(label)s%(help_text)s</li>',
            error_row='<li>%s</li>',
            row_ender='</li>',
            help_text_html=' <span class="helptext">%s</span>',
            errors_on_separate_row=False)

    def as_p(self):
        "Returns this form rendered as HTML <p>s."
        return self._html_output(
            normal_row='<p%(html_class_attr)s>%(label)s %(field)s%(help_text)s</p>',
            checked_row='<p%(html_class_attr)s>%(field)s %(label)s%(help_text)s</p>',
            error_row='%s',
            row_ender='</p>',
            help_text_html=' <span class="helptext">%s</span>',
            errors_on_separate_row=True)


NomineeFormSet = inlineformset_factory(
        Voter,
        Nominee,
        form=NomineeForm,
        extra=1,
        can_delete=True,
    )