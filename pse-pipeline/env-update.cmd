@echo off

call activate havos
call conda env list

call conda env update -f env-havos.yml
