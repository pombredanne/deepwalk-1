#!/usr/bin/python
import os
import click
import csv
from magic import Magic

class Scanner:
    def __init__(self, **options):
        self.options = options
        self.mime = options['mime']
        self.magic = Magic(magic_file='magic.db', mime=self.mime, uncompress=True)
        self._reset()

    def _reset(self):
        self.types = {}
        self.files = {}
        self.total = 0

    def scan_file(self, file):
        return self.magic.from_file(file)

    def scan(self, path):
        for root, directory, files in os.walk(path):
            for file in files:
                self.total += 1
                path = os.path.join(root, file)
                mime = self.scan_file(path)
                if not mime in self.types: self.types[mime] = []
                self.files[path] = {}
                self.files[path]['mime'] = mime
                self.types[mime].append(path)


class Reporter:
    def __init__(self, options, scanner):
        self.options = options
        self.scanner = scanner
        self.outfile = options['target']

    def report(self):
        raise NotImplemented()


class ReportCSV(Reporter):
    def report(self):
        writer = csv.writer(self.options['target'])

        headers = ["filename", ["type", "mimetype"][self.scanner.mime]]

        writer.writerow(headers)
        for f, details in self.scanner.files.iteritems():
            line = [f, details['mime']]
            writer.writerow(line)



class ReportAggregate(Reporter):
    def report(self):
        for t, fs in self.scanner.types.iteritems():
            self.outfile.write("%-35s: %d (%d%%)\n" % (t, len(fs),
                len(fs)*100/self.scanner.total))


outputmodes = {
    "csv":      ReportCSV,
    "report":   ReportAggregate,
}

@click.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('--mime', is_flag=True, help="Show mime types")
@click.option('--format', type=click.Choice(outputmodes.keys()),
    default="report", help="Choose output format")
@click.option('--target', type=click.File('w'), default='-')
def main(path, **options):
    scanner = Scanner(**options)
    scanner.scan(path)
    reporter = outputmodes[options['format']](options, scanner)
    reporter.report()


if __name__ == "__main__":
    main()
