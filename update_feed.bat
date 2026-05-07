@echo off

cd /d C:\GitHub\azienda-speciale-rss

echo ============================ >> log.txt
echo AVVIO %date% %time% >> log.txt

REM Genera nuovo feed
python generate_feed.py >> log.txt 2>&1

REM Controlla modifiche
git diff --quiet feed.xml

IF %ERRORLEVEL% EQU 0 (

    echo Nessuna modifica al feed >> log.txt
    echo COMPLETATO %date% %time% >> log.txt
    echo ============================ >> log.txt

    exit /b

)

echo Nuove modifiche trovate >> log.txt

git add feed.xml >> log.txt 2>&1

git commit -m "Aggiornamento automatico feed RSS" >> log.txt 2>&1

git push >> log.txt 2>&1

echo COMPLETATO %date% %time% >> log.txt
echo ============================ >> log.txt