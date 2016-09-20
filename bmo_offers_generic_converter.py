#!/usr/bin/python
# BMO-Offer-Convert-to-Generic.py
# Version: 2016-08-11 01
# Chris.Conser@Mastercard.com

import codecs, csv, os, re, sys, time, json

from datetime import date

today = date.today ()

#INPUT_FILE = sys.argv[1]

replacements = [['BMO Mastercard', 'card'], # en_CA
                ['BMO MasterCard', 'card'], # en_CA
                ['Mastercard BMO', 'carte'], # fr_CA
                ['MasterCard BMO', 'carte'], # fr_CA
                ["<span style=\\\\'white-space: nowrap; line-height:1.2em;\\\\'>", ''],
                ['</span>', ''],
                ['&nbsp;', chr(160)], # use non-breaking space character
                [',PENDING,', ',APPROVED,']] # Scotiabank does not use FI Dashboard Offer Review

verifications = [[' BMO', 0], ['BMO ', 0], ['Mastercard', 0], ['<span', 0], ['span>', 0], ['nbsp', 0]]


def convert(input_file, output_dir): 
    offersoutnameprefix = 'scotiacan-offers-' + today.strftime ('%Y%m%d') 
    offersoutname = offersoutnameprefix + '.csv'
    utf8intermediateoutname = offersoutnameprefix + '-utf-8-tsv INTERMEDIATE.txt'
    utf16exceloutname = offersoutnameprefix + '-utf-16-tsv EXCEL.txt'

    offersoutnamepath = output_dir + offersoutname
    utf8intermediateoutnamepath = output_dir + utf8intermediateoutname
    utf16exceloutnamepath = output_dir + utf16exceloutname

    offersin = codecs.open (input_file, mode='r', encoding='utf-8')
    offersoutcsv = codecs.open (offersoutnamepath, mode='w', encoding='utf-8')

    
    fatalverifications = 0
    offersAIRMILES = 0
    offerswithreplacements = 0
    
    log = []


    for line in offersin:
        linereplacements = 0
        log.append(line.split(',')[5] + ', ' + line.split (',')[3])
        if (re.findall ('AIR&nbsp;MILES', line, flags=re.IGNORECASE) or re.findall ('AIR MILES', line, flags=re.IGNORECASE)):
            log.append('REMOVED: AIR MILES offer.')
            offersAIRMILES = offersAIRMILES + 1
        else:
            for replacement in replacements:
                if re.findall (re.escape(replacement[0]), line):
                    line = line.replace (replacement[0], replacement[1])
                    log.append('Replaced: one or more \"' + replacement [0] + '\" mention(s) with \"' + replacement[1] + '\".')
                    linereplacements = linereplacements + 1
            for verification in verifications:
                if re.findall (verification[0], line, flags=re.IGNORECASE):
                    log.append('FATAL: still mentions \"' + verification[0] + '\" (case-insensitive) after replacement.')
                    verification[1] = verification[1] + 1
                    fatalverifications = fatalverifications + 1
            if linereplacements > 0:
                offerswithreplacements = offerswithreplacements + 1
            offersoutcsv.write (line)
        log.append('')

    offersin.close ()
    offersoutcsv.close ()

    # Convert CSV UTF-8 to TSV UTF-8 as an Intermediate Step

    offersoutcsv = open (offersoutnamepath, mode='r')
    offersouttsv = open (utf8intermediateoutnamepath, mode='w')

    csv.writer(offersouttsv, delimiter='\t').writerows(csv.reader(offersoutcsv))

    offersoutcsv.close ()
    offersouttsv.close ()

    # Convert TSV UTF-8 to UTF-16 for Easy Import to Excel That Preserves Special Characters

    offersouttsv = codecs.open (utf8intermediateoutnamepath, mode='r', encoding='utf-8')
    offersouttsvutf16 = codecs.open (utf16exceloutnamepath, mode='w', encoding='utf-16')

    for line in offersouttsv:
        offersouttsvutf16.write (line)

    offersouttsv.close ()
    offersouttsvutf16.close ()
    os.remove (utf8intermediateoutnamepath)

    response = {}

    summary = []

    summary.append('SUMMARY')
    summary.append('AIR MILES offer(s) removed: ' + str (offersAIRMILES) + '.')
    summary.append('Offer(s) with replaced mentions: ' + str (offerswithreplacements) + '.')
    summary.append('FAILED VERIFICATIONS, do not upload to Hue until resolved if greater than zero: ' + str (fatalverifications) + '.')

    if fatalverifications > 0:
        for verification in verifications:
            if verification[1] > 0:
                summary.append('   Offer(s) still mentioning \"' + verification[0] + '\" (case-insensitive) after replacement: ' + str (verification[1]) + '.')
    summary.append('Files')
    summary.append('   Review in Excel (without corrupting special characters): \"' + utf16exceloutname + '\".')
    summary.append('   Load to Hue: \"' + offersoutname + '\".')

    response['log'] = log
    response['summary'] = summary
    response['failures'] = fatalverifications
    if fatalverifications == 0:
        response['offersoutname'] = offersoutname
        response['utf16exceloutname'] = utf16exceloutname
    return json.dumps(response)

#convert(INPUT_FILE)
