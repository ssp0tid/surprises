from setuptools import setup, find_packages

setup(
    name='local-ca',
    version='1.0.0',
    description='Self-hosted Certificate Authority management tool',
    author='Local CA Team',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'cryptography>=41.0.0',
        'Flask>=3.0.0',
        'click>=8.1.0',
        'python-dateutil>=2.8.0',
    ],
    entry_points={
        'console_scripts': [
            'local-ca=local_ca.cli:main',
        ],
    },
    python_requires='>=3.9',
)
