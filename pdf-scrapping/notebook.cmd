@echo off

title PDF Processor Jupyter Notebook

call activate env-pdf-download
call conda env list
call jupyter notebook
