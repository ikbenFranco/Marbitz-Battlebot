@echo off
echo Running Marbitz Battlebot tests...
python -m pytest --cov=marbitz_battlebot --cov-report=term-missing
echo.
echo Test run complete!