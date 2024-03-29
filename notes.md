# Installing Without Sudo

This is a set of personal notes to get things to work on a machine without sudo access and with a version of python that is too old.

## Install virtualenv

virtualenv is installed via normal pip

`python -m pip install virtualenv`

## Compile and install openssl:
https://github.com/openssl/openssl/blob/master/INSTALL.md#building-openssl
```
wget https://www.openssl.org/source/openssl-1.1.1s.tar.gz
tar -zxvf openssl-1.1.1s.tar.gz
cd openssl-1.1.1s
./config --prefix=$HOME/bin/openssl 
OR ./Configure linux-x86_64 --prefix=$HOME/bin/openssl
make
make install
```

## Compile and install python:
Compiling python version via https://stackoverflow.com/a/11301911 "Use different Python version with virtualenv"
Replacing python version with tarball from https://www.python.org/downloads/ obviously
```
wget https://www.python.org/ftp/python/3.11.1/Python-3.11.1.tgz
tar -zxvf Python-3.11.1.tgz
cd Python-3.11.1
./configure --prefix=$HOME/bin/python --with-openssl=$HOME/bin/openssl --with-openssl-rpath=auto --enable-optimizations
make
make install
```

## Init virtualenv
`virtualenv venv --python=$HOME/bin/python/bin/python3`

## Run virtualenv
`source venv/bin/activate`

TODO write a quick bash script to combine this with just running the bot

## Copy Certs
May need to copy existing certs. Try the below command normally and in virtualenv:
`python -c "import ssl; print(ssl.get_default_verify_paths())"`
If the path in virtualenv doesn't have certs, gonna have problems. Copy the old (non-venv) `certs` directory contents into the certs directory of the openssl compilation.

## Install discord.py
https://discordpy.readthedocs.io/en/stable/intro.html
`pip install -U discord.py`



