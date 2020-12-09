import click
import requests
import logging

from utils import (
    replace_regex,
    replace_simple,
    replace_list,
    read_yaml_from_url,
    delete_line,
    file_contains,
    append_to_file,
    add_line,
    delete_file,
    render_template,
    build_template,
    render_and_copy_template,
)

from config import (
    REPO_PATHS_TO_MIGRATE,
)

logging.basicConfig(level=logging.INFO)


def migrate_repo(path):
    """Perform migration to repo on given path."""

    click.secho(f"\n>>> Migrating {path}...", fg="green")

    repo = path.split("/")[-1]
    repo_underscores = repo.replace("-", "_")

    if path[-1] != "/":
        path += "/"

    # pypi-publish.yml
    travis_url = (
        f"https://raw.githubusercontent.com/inveniosoftware/{repo}/master/.travis.yml"
    )
    travis = read_yaml_from_url(travis_url)
    if travis and travis.get("deploy", {}).get("provider") == "pypi":
        has_compile_catalog = "compile_catalog" in travis.get("deploy", {}).get(
            "distributions"
        )
        logging.info(f"Has `compile_catalog` in travis.yml?: {has_compile_catalog}")
        render_and_copy_template(
            "pypi-publish.yml",
            {"has_compile_catalog": has_compile_catalog},
            f"{path}.github/workflows",
        )

    # .editorconfig
    replace_simple(path + ".travis.yml", ".github/workflows/*.yml", ".editorconfig")

    # README.rst
    replace_regex(
        r"https:\/\/img\.shields\.io\/travis\/([a-z]*\/[a-z-]*)\.svg",
        "https://github.com/\\1/workflows/CI/badge.svg",
        path + "README.rst",
    )
    replace_regex(
        r"https:\/\/travis-ci\.org\/([a-z]*\/[a-z-]*)",
        "https://github.com/\\1/actions?query=workflow%3ACI",
        path + "README.rst",
    )

    # CONTRIBUTING.rst
    replace_regex(
        r"https:\/\/travis-ci\.(org|com)\/([a-z]*\/[a-z-]*)\/pull_requests",
        "https://github.com/\\2/actions?query=event%3Apull_request",
        path + "CONTRIBUTING.rst",
    )

    # tests.yaml
    build_template(repo, "tests.yml", dest_path=f"{path}.github/workflows")
    # run-tests.sh
    build_template(repo, "run-tests.sh", dest_path=path)

    # pytest.ini
    delete_line("pep8ignore", path + "pytest.ini")
    replace_regex(
        "(addopts =).*",
        f'\\1 --isort --pydocstyle --pycodestyle --doctest-glob="*.rst" --doctest-modules --cov={repo_underscores} --cov-report=term-missing',
        path + "pytest.ini",
    )
    if not file_contains("testpaths", path + "pytest.ini"):
        append_to_file(f"testpaths = tests {repo_underscores}", path + "pytest.ini")

    # Add .github/workflows *.yml to MANIFEST.in
    add_line("recursive-include .github/workflows *.yml\n", path + "MANIFEST.in")

    # Delete travis file
    delete_file(path + ".travis.yml")

    # Upgrade Sphinx 1 to 3 in setup.py
    replace_regex(
        r"Sphinx>=1.[0-9](.[0-9])?.*,",
        "Sphinx>=3',",
        path + "setup.py",
    )

    # Simplify setup.py test requirements replacing them with pytest-invenio
    replace_list(
        path + "setup.py",
        r"tests_require = (['\"\'[\s*\"(a-z-A-Z><=0-9.\[\]),]*])",
        [
            # Remove packages already installed by pytest-invenio
            "check-manifest",
            "coverage",
            "docker-services-cli",
            "pytest-celery",
            "pytest-cov",
            "pytest-flask",
            "pytest-isort",
            "pytest-pycodestyle",
            "pytest-pydocstyle",
            "pydocstyle",
            "pytest",
            "selenium",
            # pytest-pep8 is replaced by pytest-pycodestyle
            "pytest-pep8",
            # pytest-pep8 is replaced by pytest-isort
            "isort",
        ],
        ["pytest-invenio>=1.4.0"],
        "tests_require",
    )

    # Remove bak files
    delete_file(path + "*.bak")


@click.command()
@click.option("--targetpath", help="Target repo directory path")
def pipeline(targetpath):
    """Helps the migration from Travis CI pipelines
    to GitHub Actions running some common tasks"""

    if targetpath:
        migrate_repo(targetpath)
    else:
        for repo_path in REPO_PATHS_TO_MIGRATE:
            migrate_repo(repo_path)


if __name__ == "__main__":
    pipeline()
