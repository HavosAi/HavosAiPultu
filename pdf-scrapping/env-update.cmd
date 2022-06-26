@echo off

call activate env-pdf-download
call conda env list

call conda env update -f env-pdf-download.yml
