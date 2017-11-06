#!/usr/bin/env python
import sys
import os
import argparse
from subprocess import check_call


parser = argparse.ArgumentParser(description='Create/Recreate a conda environment and a module file for it.',
                                 epilog='The resulting environment name and module name will be package-version. Note that there can be cases where it\'s advantageous to specify that additional packages be installed in a given environment. In such cases, specify them under "other params", such as bowtie2==1.1.1.')
parser.add_argument('package', help='A package name, which must be present in bioconda or conda-forge')
parser.add_argument('version', help='A version, such as 1.0.0')
parser.add_argument('-n', metavar='Environment Name', dest='envName', help='For consistency, if the package name does not match the desired environment name, then you can manually set the environment name here (e.g., "Salmon" rather than "salmon")', required=False)
parser.add_argument('other_params', nargs=argparse.REMAINDER, help='All other options are passed directly to "conda env create". This is optional and can be used to add other requirements that you don\'t want included in the environment name.')

args = parser.parse_args()

envBaseName = args.package
if args.envName:
    envBaseName = args.envName

envName = '{}-{}'.format(envBaseName, args.version)
package_version = '{}=={}'.format(args.package, args.version)

# Check if the env already exists
if os.path.exists('/package/anaconda3/envs/{}'.format(envName)):
    cmd = ['/package/anaconda3/bin/conda', 'env', 'remove', '-n', envName, '-y']
    check_call(cmd)

# Create the conda environment
cmd = ['/package/anaconda3/bin/conda', 'create', '-y', '-q', '--force', '-n', envName]

try:
    check_call(cmd)
except:
    sys.stderr.write('An error occurred while creating the conda environment:\n')
    sys.stderr.write('{}'.format(sys.exc_info()[0]))
    sys.stderr.write('\n')
    sys.exit(1)

# Install into the conda environment
cmd = ['/package/anaconda3/bin/conda', 'install', '-n', envName, '-y', '-q', package_version]

if args.other_params:
    cmd.extend(args.other_params)

try:
    check_call(cmd)
except:
    sys.stderr.write('An error occurred while installing into the conda environment:\n')
    sys.stderr.write('{}'.format(sys.exc_info()[0]))
    sys.stderr.write('\n')
    sys.exit(1)


# Make the environment module
try:
    os.makedirs('/usr/share/Modules/modulefiles/{}'.format(envBaseName))
except:
    pass
f = open('/usr/share/Modules/modulefiles/{}/{}'.format(envBaseName, args.version), 'w')

template = '''#%Module1.0
proc ModulesHelp {{ }} {{
puts stderr "Adds {package}-{version} to your PATH."
}}

module-whatis   "Adds {package}-{version} to your PATH."

prepend-path    PATH    /package/anaconda3/envs/{package}-{version}/bin
setenv CONDA_PREFIX /package/anaconda3/envs/{package}-{version}
setenv CONDA_DEFAULT_ENV {package}-{version}
'''

d = {'package': envBaseName, 'version': args.version}

f.write(template.format(**d))
f.close()

f = open('/usr/share/Modules/modulefiles/{}/.version'.format(envBaseName), 'w')
f.write('#%Module1.0\nset ModulesVersion {}\n'.format(args.version))
f.close()
