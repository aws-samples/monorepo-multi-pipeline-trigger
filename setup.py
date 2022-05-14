import setuptools


with open("README.md") as fp:
    long_description = fp.read()


setuptools.setup(
    name="monorepo_codepipeline_trigger",
    version="0.0.1",

    description="CodeCommit monorepo multi pipeline triggers",
    long_description=long_description,
    long_description_content_type="text/markdown",

    author="author",

    package_dir={"": "."},
    packages=setuptools.find_packages(where="monorepo_codepipeline_trigger"),

    install_requires=[
        "aws-cdk-lib>=2.0.0",
        "constructs>=10.0.0"
    ],

    python_requires=">=3.6",

    classifiers=[
        "Development Status :: 4 - Beta",

        "Intended Audience :: Developers",

        "Programming Language :: JavaScript",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",

        "Topic :: Software Development :: Code Generators",
        "Topic :: Utilities",

        "Typing :: Typed",
    ],
)
