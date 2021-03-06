"""Post-generate hook for cookiecutter."""
from os import listdir
from os.path import join
from subprocess import CalledProcessError, check_call, check_output, STDOUT

import logging
import shutil
import sys


def shell(command, capture=False):
    """Portable system call that aborts generation in case of failure."""
    try:
        if capture:
            stdout = check_output(command, shell=True, stderr=STDOUT,
                                  universal_newlines=True)
            return str(stdout)
        else:
            check_call(command, shell=True)
    except CalledProcessError as err:
        LOG.error('Project generation failed.')
        sys.exit(err.returncode)


def set_up_ci_service():
    """If a framework project was created move it to project root."""
    ci_service = '{{ cookiecutter.ci_service }}'

    if ci_service == 'codeship-steps.yml':
        LOG.info('Adding additional files for this CI setup ...')
        ci_services_folder = join('_', 'ci-services')
        shutil.move(join(ci_services_folder, 'codeship-services.yml'), '.')


def set_up_framework():
    """If a framework project was created move it to project root."""
    framework = '{{ cookiecutter.framework }}'
    if framework == '(none)':
        return

    LOG.info('Moving files for %s project ...', framework)
    framework_folder = join('_', 'frameworks', framework)
    for file_or_folder in listdir(framework_folder):
        shutil.move(join(framework_folder, file_or_folder), '.')


def set_up_deployment():
    """
    If a framework project was created also move deployment configuration
    to project root.
    """
    framework_technology = {
        'Django': 'python',
        'Flask': 'python',
        'PHP-generic': 'php',
    }
    framework = '{{ cookiecutter.framework }}'

    try:
        technology = framework_technology[framework]
    except KeyError:
        LOG.warning('Skipping deployment configuration: '
                    'No framework specified.')
        return

    LOG.info('Moving deployment configuration for %s project ...', framework)
    deployment_folder = join('_', 'deployment', technology)
    for file_or_folder in listdir(deployment_folder):
        shutil.move(join(deployment_folder, file_or_folder), '.')


def remove_temporary_files():
    """Remove files and folders only needed as input for generation."""
    LOG.info('Removing input data folder ...')
    shutil.rmtree('_')


def init_version_control():
    """Initialize a repository, commit the code, and prepare for pushing."""
    vcs_info = {
        'platform_name': '{{ cookiecutter.vcs_platform }}',
        'platform': '{{ cookiecutter.vcs_platform.lower() }}',
        'account': '{{ cookiecutter.vcs_account }}',
        'project': '{{ cookiecutter.project_slug }}',
    }
    vcs_info['remote_uri'] = \
        'git@{platform}:{account}/{project}.git'.format(**vcs_info)
    vcs_info['web_url'] = \
        'https://{platform}/{account}/{project}'.format(**vcs_info)

    LOG.info('Initializing version control ...')
    shell('git init --quiet')
    shell('git add .')

    output = shell('git config --list', capture=True)
    if 'user.email=' not in output:
        LOG.warning('I need to add user.email. BEWARE! Check with:'
                    ' git config --list')
        shell('git config user.email "{{ cookiecutter.email }}"')
    if 'user.name=' not in output:
        LOG.warning('I need to add user.name. BEWARE! Check with:'
                    ' git config --list')
        shell('git config user.name "{{ cookiecutter.full_name }}"')

    shell('git commit --quiet'
          ' -m "Initial commit by Painless Continuous Delivery"')
    shell('git remote add origin {remote_uri}'.format(**vcs_info))
    LOG.info("You can now create a project '%(project)s' on %(platform_name)s."
             " %(web_url)s", vcs_info)
    LOG.info('Then push the code to it: $ git push -u origin --all')


def set_git_hook_dir():
    """ Sets the directory for the git hooks."""
    shell('git config core.hooksPath .githooks')
    LOG.info('Setting the git hook dir to .githooks')

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(message)s')
    LOG = logging.getLogger('post_gen_project')

    set_up_ci_service()
    set_up_framework()
    set_up_deployment()
    remove_temporary_files()
    init_version_control()
    set_git_hook_dir()
