"""Test generating a project."""
from os import system
from os.path import dirname, join
from filecmp import cmp as compare_files

REPO_ROOT = dirname(dirname(__file__))


def pytest_generate_tests(metafunc):
    """
    A test scenarios implementation for py.test, as found at
    http://docs.pytest.org/en/latest/example/parametrize.html
    #a-quick-port-of-testscenarios.  Picks up a ``scenarios`` class variable
    to parametrize all test function calls.
    """
    idlist = []
    argvalues = []
    for scenario in metafunc.cls.scenarios:
        idlist.append(scenario[0])
        items = scenario[1].items()
        argnames = [x[0] for x in items]
        argvalues.append(([x[1] for x in items]))
    metafunc.parametrize(argnames, argvalues, ids=idlist, scope="class")


# pylint: disable=too-few-public-methods
class TestCISetup(object):
    """
    Tests for verifying generated CI setups of this cookiecutter,
    executed several times with different values (test scenarios).
    """
    scenarios = [
        ('codeship', {
            'project_slug': 'myproject',
            'vcs_account': 'painless-software',
            'vcs_platform': 'Bitbucket.org',
            'vcs_remote': 'git@bitbucket.org:painless-software/myproject.git',
            'ci_service': 'codeship-steps.yml',
            'ci_testcommand': '  service: app',
            'tests': 'flake8,pylint,py27,py33,py34,py35,pypy',
        }),
        ('gitlab', {
            'project_slug': 'myproject',
            'vcs_account': 'painless-software',
            'vcs_platform': 'GitLab.com',
            'vcs_remote': 'git@gitlab.com:painless-software/myproject.git',
            'ci_service': '.gitlab-ci.yml',
            'ci_testcommand': '  script: tox',
            'tests': 'flake8,pylint,py27,py33,py34,py35,pypy',
        }),
        ('shippable', {
            'project_slug': 'myproject',
            'vcs_account': 'painless-software',
            'vcs_platform': 'Bitbucket.org',
            'vcs_remote': 'git@bitbucket.org:painless-software/myproject.git',
            'ci_service': 'shippable.yml',
            'ci_testcommand': '    - tox',
            'tests': 'flake8,pylint,py27,py33,py34,py35,pypy',
        }),
        ('travis', {
            'project_slug': 'myproject',
            'vcs_account': 'painless-software',
            'vcs_platform': 'GitHub.com',
            'vcs_remote': 'git@github.com:painless-software/myproject.git',
            'ci_service': '.travis.yml',
            'ci_testcommand': 'script: tox',
            'tests': 'flake8,pylint,py27,py33,py34,py35,pypy',
        }),
        ('vexor', {
            'project_slug': 'myproject',
            'vcs_account': 'painless-software',
            'vcs_platform': 'GitHub.com',
            'vcs_remote': 'git@github.com:painless-software/myproject.git',
            'ci_service': 'vexor.yml',
            'ci_testcommand': 'script: tox',
            'tests': 'flake8,pylint,py27,py33,py34,py35,pypy',
        }),
    ]

    # pylint: disable=too-many-arguments,too-many-locals,no-self-use
    def test_ci_setup(self, cookies, project_slug,
                      vcs_account, vcs_platform, vcs_remote,
                      ci_service, ci_testcommand, tests):
        """
        Generate a CI setup with specific settings and verify it is complete.
        """
        result = cookies.bake(extra_context={
            'project_slug': project_slug,
            'vcs_platform': vcs_platform,
            'vcs_account': vcs_account,
            'ci_service': ci_service,
            'tests': tests,
        })

        assert result.exit_code == 0
        assert result.exception is None

        assert result.project.basename == project_slug
        assert result.project.isdir()
        assert result.project.join('README.rst').isfile()

        assert result.project.join('.git').isdir()
        assert result.project.join('.gitignore').isfile()
        git_config = result.project.join('.git', 'config').readlines(cr=False)
        assert '[remote "origin"]' in git_config
        assert '\turl = {}'.format(vcs_remote) in git_config

        tox_ini = result.project.join('tox.ini').readlines(cr=False)
        assert '[tox]' in tox_ini
        assert 'envlist = {}'.format(tests) in tox_ini
        assert '[testenv]' in tox_ini
        assert '[testenv:flake8]' in tox_ini
        assert '[testenv:pylint]' in tox_ini

        ci_service_conf = result.project.join(ci_service).readlines(cr=False)
        assert ci_testcommand in ci_service_conf

        # ensure this project itself stays up-to-date with the template
        file_list = ['.gitignore', 'docker-compose.yml', 'tox.ini', ci_service]
        for filename in file_list:
            mother_file = join(REPO_ROOT, filename)
            generated_file = result.project.join(filename).strpath
            assert compare_files(mother_file, generated_file), \
                "Mother project '{}' not matching template.\n {} != {}".format(
                    filename, mother_file, generated_file)


# pylint: disable=too-few-public-methods
class TestFramework(object):
    """
    Tests for verifying generated projects using specific Web frameworks.
    """
    scenarios = [
        ('flask', {
            'project_slug': 'flask-project',
            'vcs_account': 'painless-software',
            'vcs_platform': 'GitHub.com',
            'ci_service': '.travis.yml',
            'framework': 'Flask',
        }),
    ]

    # pylint: disable=too-many-arguments,too-many-locals,no-self-use
    def test_framework(self, cookies, project_slug, vcs_account, vcs_platform,
                       ci_service, framework):
        """
        Generate a framework project and verify it is complete and working.
        """
        result = cookies.bake(extra_context={
            'project_slug': project_slug,
            'vcs_platform': vcs_platform,
            'vcs_account': vcs_account,
            'ci_service': ci_service,
            'framework': framework,
        })

        assert result.exit_code == 0
        assert result.exception is None

        requirements_file = result.project.join('requirements.txt')
        assert requirements_file.isfile()
        exit_code = system('pip install -r %s' % requirements_file.realpath())
        assert exit_code == 0, 'Installing requirements failed.'
