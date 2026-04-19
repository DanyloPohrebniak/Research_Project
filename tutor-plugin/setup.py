from setuptools import setup, find_packages

setup(
    name="tutor-contrib-chatbot",
    version="0.1.0",
    description="AI Chatbot plugin for Tutor Open edX",
    packages=find_packages(),
    install_requires=["tutor>=18.0.0"],
    entry_points={
        "tutor.plugin.v1": [
            "chatbot = tutorchatbot"
        ]
    },
    package_data={
        "tutorchatbot": ["templates/**/*"],
    },
)