import fileinput
import glob
import logging
import re
import os

import requests
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


def delete_line(term, filepath):
    """Delete file line contaning given term."""
    logging.info(f"TASK: Deleting line containing {term} in {filepath}")
    # import wdb; wdb.set_trace()
    if not os.path.isfile(filepath):
        logging.info("No %s found" % filepath)
    else:
        logging.info("Found %s" % filepath)
        with open(filepath, "r") as f:
            lines = f.readlines()
        with open(filepath, "w") as f:
            for line in lines:
                if term not in line:
                    f.write(line)
                else:
                    logging.info(f"TASK: Line deleted")


def add_line(term, filepath):
    """ Add a line to a file """
    logging.info("TASK: Adding line '%s' to %s" % (term, filepath))
    # If the file exists
    if os.path.isfile(filepath):
        # And the line is not already there
        if not file_contains(term, filepath):
            append_to_file(term, filepath)
        else:
            logging.info("SKIPPED TASK. Line already there. ")
    else:
        logging.info("SKIPPED TASK. No %s found" % filepath)


def file_contains(term, filepath):
    """Check whether file contains given term."""
    with open(filepath) as f:
        return term in f.read()


def append_to_file(text, filepath):
    """Append text to file."""
    with open(filepath, "a") as f:
        f.write(text)


def replace_simple(text, replacing, filepath):
    """
    Replaces every match of a string with another in the specified file
    """
    logging.info(
        "TASK: Simple replacing %s with %s in %s" % (text, replacing, filepath)
    )
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
    logging.info(
        "TASK: RegEx replacing %s with %s in %s" % (regex, output, filepath)
    )
    if os.path.isfile(filepath):
        logging.info("Found %s" % filepath)
        # TODO: expose number of matches
        with fileinput.FileInput(filepath, inplace=True, backup=".bak") as file:
            for line in file:
                print(re.sub(regex, output, line), end="")
    else:
        logging.info("SKIPPED TASK. No %s found" % filepath)


def download_file(url, destination):
    # Get path
    dirname = os.path.dirname(os.path.realpath(destination))
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    print(dirname)
    r = requests.get(url, allow_redirects=True)
    open(destination, "wb").write(r.content)


@click.command()
@click.option("--targetpath", default=".", help="Target repo directory path")
def pipeline(targetpath):
    """Helps the migration from Travis CI pipelines
    to GitHub Actions running some common tasks"""

    repo = targetpath.split("/")[-1]
    repo_underscores = repo.replace("-", "_")

    # TODO: add the trailing slash only if needed
    targetpath = targetpath + "/"
    # Reference: https://codimd.web.cern.ch/TOOkF5yhSAKJq3TiY0L42A?view

    # .editorconfig
    replace_simple(
        targetpath + ".travis.yml", ".github/workflows/*.yml", ".editorconfig"
    )

    # README.rst
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

    # CONTRIBUTING.rst
    replace_regex(
        r"https:\/\/travis-ci\.(org|com)\/([a-z]*\/[a-z-]*)\/pull_requests",
        "https://github.com/\\2/actions?query=event%3Apull_request",
        targetpath + "CONTRIBUTING.rst",
    )

    # run-tests.sh
    delete_line("isort", targetpath + "run-tests.sh")
    replace_simple(
        'check-manifest --ignore ".travis-*"',
        'check-manifest --ignore ".*-requirements.txt"',
        targetpath + "run-tests.sh",
    )

    # Download tests.yml template
    download_file(
        "https://raw.githubusercontent.com/inveniosoftware/.github/master/workflow-templates/tests.yml",
        targetpath + ".github/workflows/tests.yml",
    )

    # Download pypi-publish.yml template
    download_file(
        "https://raw.githubusercontent.com/inveniosoftware/.github/master/workflow-templates/pypi-publish.yml",
        targetpath + ".github/workflows/pypi-publish.yml",
    )

    # pytest.ini
    delete_line("pep8ignore", targetpath + "pytest.ini")
    replace_regex(
        "(addopts =).*",
        f'\\1 --isort --pydocstyle --pycodestyle --doctest-glob="*.rst" --doctest-modules --cov={repo_underscores} --cov-report=term-missing tests {repo_underscores}',
        targetpath + "pytest.ini",
    )
    if not file_contains("testpaths", targetpath + "pytest.ini"):
        append_to_file(
            f"testpaths = tests {repo_underscores}", targetpath + "pytest.ini"
        )

    #
    add_line(
        "recursive-include .github/workflows *.yml", targetpath + "MANIFEST.in"
    )

    # Delete travis file
    delete_file(targetpath + ".travis.yml")

    # Remove bak files
    delete_file(targetpath + "*.bak")


if __name__ == "__main__":
    pipeline()
