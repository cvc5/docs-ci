#!/usr/bin/env python3

import datetime
import glob
import jinja2
import os
import re
import subprocess

tpl_str = """
{% if trigger %}
* [Documentation for {{ trigger.name }}]({{ trigger.path }}/) (built from [{{ trigger.commit }}]({{ trigger.commitlink }}) @ [{{ trigger.name }}]({{ trigger.link}}), {{ trigger.date }})

***
{% endif %}

{% for entry in entries -%}
* [Documentation for {{ entry.name }}]({{ entry.path }}/) (built from [{{ entry.commit }}]({{ entry.commitlink }}) @ [{{ entry.name }}]({{ entry.link}}), {{ entry.date }})
{% endfor %}
"""

BASE_URL = 'https://github.com/cvc5/cvc5'

trigger = None

entries = []
for folder in glob.iglob('docs-*'):
    if not os.path.islink(folder):
        continue
    m = re.match('^docs-pr([0-9]+)$', folder)
    prid = 0
    if m is not None:
        prid = int(m.group(1))
        name = 'PR #{}'.format(prid)
        link = '{}/pull/{}'.format(BASE_URL, prid)
    else:
        name = folder[5:]
        link = '{}/tree/{}'.format(BASE_URL, name)
    target = os.readlink(folder)
    assert target.startswith(folder)
    commit = target[len(folder) + 1:][:7]
    date = subprocess.check_output(['git', 'log', '-1', 'HEAD', '--pretty=%ar', target]).decode().strip()
    if date == '':
        staged = subprocess.check_output(['git', 'diff', '--name-only', '--cached', target]).decode().strip()
        if staged == '':
            date = 'not committed'
        else:
            date = 'now'
    entries.append({
        'path': folder,
        'name': name,
        'link': link,
        'commit': commit,
        'commitlink': '{}/commit/{}'.format(BASE_URL, commit),
        'prid': -prid,
        'date': date,
    })
    if date == 'now':
        trigger = {
            **entries[-1],
            'date': datetime.datetime.now(datetime.timezone.utc).strftime('%b %a %d, %H:%M %Z'),
        }

entries.sort(key=lambda e: (e['name'].startswith('PR #'), e['prid'], e['name']))

tpl = jinja2.Template(tpl_str)
out = tpl.render(entries=entries, trigger=trigger)
open('README.md', 'w').write(out)
