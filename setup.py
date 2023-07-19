from setuptools import setup

setup(
    name='ankibox',
    version='1.0.1',
    description='turn notes into anki cards',
    packages=['ankibox'],
    install_requires=['tomli',
                      ],
    entry_points=(
        """
        [console_scripts]
        ankibox = ankibox.ankibox:main
        """
    )
)