import fileinput
import glob
import logging
import re
import os

import click

logging.basicConfig(level=logging.DEBUG)


def delete_file(filepath):
    """
    If a file exists, delete it
    """
    logging.info("TASK: Deleting %s" % filepath)
    for file in glob.glob(filepath):
        if os.path.isfile(file):
            logging.info("Found %s" % file)
            os.remove(file)
            logging.info("Deleted %s" % file)
        else:
            logging.info("No %s found" % file)


def replace_simple(text, replacing, filepath):
    """
    Replaces every match of a string with another in the specified file
    """
    logging.info("TASK: Simple replacing %s with %s in %s" % (text, replacing, filepath))
    if os.path.isfile(filepath):
        logging.info("Found %s" % filepath)
        # TODO: expose number of matches
        with fileinput.FileInput(filepath, inplace=True, backup=".bak") as file:
            for line in file:
                print(line.replace(text, replacing), end="")
    else:
        logging.info("No %s found" % filepath)


def replace_regex(regex, output, filepath):
    """
    Replaces every match of a string with another in the specified file
    """
    logging.info("TASK: RegEx replacing %s with %s in %s" % (regex, output, filepath))
    if os.path.isfile(filepath):
        logging.info("Found %s" % filepath)
        # TODO: expose number of matches
        with fileinput.FileInput(filepath, inplace=True, backup=".bak") as file:
            for line in file:
                print(re.sub(regex, output, line), end="")
    else:
        logging.info("SKIPPED TASK. No %s found" % filepath)


@click.command()
@click.option("--targetpath", default=".", help="Target repo directory path")
def pipeline(targetpath):
    """Helps the migration from Travis CI pipelines
    to GitHub Actions running some common tasks"""

    # TODO: add the trailing slash only if needed
    targetpath = targetpath + "/"
    # Reference: https://codimd.web.cern.ch/TOOkF5yhSAKJq3TiY0L42A?view

    # Step 3
    replace_simple(targetpath + ".travis.yml", ".github/workflows/*.yml", ".editorconfig")
    # Step 4.1
    replace_regex(
        r"https:\/\/img\.shields\.io\/travis\/([a-z]*\/[a-z-]*)\.svg",
        "https://github.com/\\1/workflows/CI/badge.svg",
        targetpath + "README.rst",
    )
    replace_regex(
        r"https:\/\/travis-ci\.org\/([a-z]*\/[a-z-]*)",
        "https://github.com/\\1/actions?query=workflow%3ACI",
        targetpath + "README.rst",
    )
    # Step 4.2
    replace_regex(
        r"https:\/\/travis-ci\.(org|com)\/([a-z]*\/[a-z-]*)\/pull_requests",
        "https://github.com/\\2/actions?query=event%3Apull_request",
        targetpath + "CONTRIBUTING.rst",
    )
    # Step 5
    replace_simple(
        'check-manifest --ignore ".travis-*"',
        'check-manifest --ignore ".*-requirements.txt"',
        targetpath + "run-tests.sh",
    )

    # Delete travis file
    delete_file(targetpath + ".travis.yml")

    # Remove bak files
    delete_file(targetpath + "*.bak")


if __name__ == "__main__":
    pipeline()
