@echo off

title Havos Jupyter Notebook

call activate havos
call conda env list
call jupyter notebook
