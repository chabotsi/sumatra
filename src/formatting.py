"""
The formatting module provides classes for formatting simulation/analysis
records in different ways: summary, list or table; and in different mark-up
formats: currently text or HTML.

Classes
-------

TextFormatter - formats records as text
HTMLFormatter - formats records as HTML

Function
--------

get_formatter() - return an approriate Formatter object for a given requested
                  format.
"""

import textwrap

fields = ['label', 'reason', 'outcome', 'duration', 'repository', 'main_file',
          'version', 'script_arguments', 'executable', 'timestamp', 'tags']

class Formatter(object):
    
    def __init__(self, records):
        self.records = records
        
    def format(self, mode='short'):
        return getattr(self, mode)()


class TextFormatter(Formatter):
    
    def short(self):
        return "\n".join(record.label for record in self.records)
            
    def long(self, text_width=80, indent=17):
        output = ""
        for record in self.records:
            output += "-" * text_width + "\n"
            for field in fields:
                entryStr = "%s%d%s" % ("%-",indent,"s: ") % field.title()
                entry = getattr(record,field)
                if callable(entry):
                    entryStr += str(entry())
                elif hasattr(entry, "items"):
                    entryStr += ", ".join(["%s=%s" % item for item in entry.items()])
                elif isinstance(entry, set):
                    entryStr += ", ".join(entry)
                else:
                    entryStr += str(entry)
                output += textwrap.fill(entryStr, width=text_width,
                                        replace_whitespace=False,
                                        subsequent_indent=' '*(indent+2)) + "\n"
        return output
    
    def table(self):
        tt = TextTable(fields, self.records)
        return str(tt)
    

class TextTable(object):
    """
    Very primitive implementation of a text table. There are more sophisticated
    implementations around, e.g. http://pypi.python.org/pypi/texttable/0.6.0/
    but for now I'd like to avoid too many dependencies.
    """
    
    def __init__(self, headers, rows, max_column_width=20):
        self.headers = headers
        self.rows = rows
        self.max_column_width = max_column_width
        
    def calculate_column_widths(self):
        column_widths = []
        for header in self.headers:
            column_width = max([len(header)] + [len(str(getattr(row, header))) for row in self.rows])
            column_widths.append(min(self.max_column_width, column_width))
        return column_widths
            
    def __str__(self):
        column_widths = self.calculate_column_widths()
        format = "| " + " | ".join("%%-%ds" % w for w in column_widths) + " |\n"
        assert len(column_widths) == len(self.headers)
        output = format % tuple(h.title() for h in self.headers)
        for row in self.rows:
            output += format % tuple(str(getattr(row, header))[:self.max_column_width] for header in self.headers)
        return output
        

class HTMLFormatter(Formatter):
    
    def short(self):
        return "<ul>\n<li>" + "</li>\n<li>".join(record.label for record in self.records) + "</li>\n</ul>"
    
    def long(self):
        def format_record(record):
            output = "  <dt>%s</dt>\n  <dd>\n    <dl>\n" % record.label
            for field in fields:
                output += "      <dt>%s</dt><dd>%s</dd>\n" % (field, getattr(record, field))
            output += "    </dl>\n  </dd>"
            return output
        return "<dl>\n" + "\n".join(format_record(record) for record in self.records) + "\n</dl>"

    def table(self):
        def format_record(record):
            return "  <tr>\n    <td>" + "</td>\n    <td>".join(str(getattr(record, field)) for field in fields) + "    </td>\n  </tr>"
        return "<table>\n" + \
               "  <tr>\n    <th>" + "</th>\n    <th>".join(field.title() for field in fields) + "    </th>\n  </tr>\n" + \
               "\n".join(format_record(record) for record in self.records) + \
               "\n</table>"


class TextDiffFormatter(Formatter):
    
    def __init__(self, diff):
        self.diff = diff
        
    def short(self):
        def yn(x):
            return x and "yes" or "no"
        D = self.diff
        output = textwrap.dedent("""\
            Record 1              : %s
            Record 2              : %s
            Executable differs    : %s
            Code differs          : %s
              Repository differs  : %s
              Main file differs   : %s
              Version differs     : %s
              Non checked-in code : %s
              Dependencies differ : %s 
            Launch mode differs   : %s
            Parameters differ     : %s
            Data differs          : %s""" % (
                D.recordA.label,
                D.recordB.label,
                yn(D.executable_differs),
                yn(D.code_differs),
                yn(D.repository_differs), yn(D.main_file_differs),
                yn(D.version_differs), yn(D.diff_differs),
                yn(D.dependencies_differ),
                yn(D.launch_mode_differs),
                yn(D.parameters_differ),
                yn(D.data_differs))
            )
        return output
    
    def long(self):
        output = ''
        if self.diff.dependencies_differ:
            diffs = self.diff.dependency_differences
            output += "Dependency differences:\n"
            for name, (depA, depB) in diffs.items():
                if depA and depB:
                    output += "  %s\n" % name
                    output += "    A: version=%s\n" % depA.version
                    output += "       %s\n" % depA.diff.replace("\n", "\n       ")
                    output += "    B: version=%s\n" % depB.version
                    output += "       %s\n" % depA.diff.replace("\n", "\n       ")
                elif depB is None:
                    output += "  %s is a dependency of %s but not of %s" % (name, self.diff.recordA.label, self.diff.recordB.label)
                elif depA is None:
                    output += "  %s is a dependency of %s but not of %s" % (name, self.diff.recordB.label, self.diff.recordA.label)
                    
        diffs = self.diff.launch_mode_differences
        if diffs:
            output += "Launch mode differences:\n"
            modeA, modeB = diffs
            output += "  %s: %s\n" % (self.diff.recordA.label, modeA)
            output += "  %s: %s\n" % (self.diff.recordB.label, modeB)

        diffs = self.diff.data_differences
        if diffs:
            output += "Output data differences:\n"
            for name, (depA, depB) in diffs.items():
                if depA and depB:
                    output += "  %s\n" % name
                    output += "    A: size=%s\n" % depA.size
                    output += "    B: size=%s\n" % depB.size
                elif depB is None:
                    output += "  %s is generated by %s but not by %s" % (name, self.diff.recordA.label, self.diff.recordB.label)
                elif depA is None:
                    output += "  %s is generated by %s but not by %s" % (name, self.diff.recordB.label, self.diff.recordA.label)
        # to be completed...
        return output
    
formatters = {
    'text': TextFormatter,
    'html': HTMLFormatter,
    'textdiff': TextDiffFormatter,
}
        
def get_formatter(format):
    return formatters[format]

def get_diff_formatter():
    return TextDiffFormatter