import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
scenes={
'bigbuckbunny':('#5b7551','#c7d19e','#223e30','<circle cx="505" cy="75" r="42" fill="#e6e6bb"/><path d="M0 200Q130 80 260 190T640 160V400H0" fill="#799662"/><path d="M0 230Q170 150 340 240T640 200V400H0" fill="#3f653e"/>'),
'sintel':('#263e39','#879b7c','#112923','<circle cx="470" cy="90" r="67" fill="#d7dab2"/><path d="M0 300L150 90 230 190 330 60 470 230 550 130 640 300V400H0" fill="#3e5d50"/><path d="M0 300L210 210 330 280 430 170 640 310V400H0" fill="#1c3a30"/>'),
'tearsofsteel':('#374f5c','#819a9b','#162932','<circle cx="470" cy="100" r="50" fill="#c9c9a7"/><path d="M0 250V150H50V210H100V80H140V240H200V130H245V230H280V60H310V210H350V110H410V250H480V150H530V190H580V100H640V400H0" fill="#253e49"/><path d="M300 400L370 230 445 400" fill="#9bb1a0" opacity=".4"/>'),
'elephantsdream':('#4b4243','#b4a18b','#27272b','<g fill="none" stroke="#c3b092" opacity=".4"><circle cx="450" cy="140" r="95" stroke-width="9"/><circle cx="450" cy="140" r="55" stroke-width="15"/><path d="M0 280H230V140H450V0M300 400V270H640" stroke-width="17"/></g><path d="M0 310L640 230V400H0" fill="#2c3030"/>'),
'cosmoslaundromat':('#655776','#a6a1bc','#272b42','<circle cx="450" cy="100" r="65" fill="#c9be9d"/><ellipse cx="450" cy="100" rx="120" ry="20" fill="none" stroke="#c1b49d" stroke-width="10" transform="rotate(-24 450 100)"/><path d="M0 250Q130 170 300 260T640 210V400H0" fill="#596451"/><path d="M0 300Q200 210 450 320L640 270V400H0" fill="#354b3b"/>'),
'spring':('#53684d','#b9c899','#253d33','<circle cx="430" cy="90" r="55" fill="#e0d9a1"/><g fill="#3b6144"><path d="M30 300L100 40 170 300ZM130 300L215 80 300 300ZM400 300L485 25 570 300ZM510 300L590 75 670 300Z"/></g><path d="M0 300Q300 180 640 280V400H0" fill="#2a4936"/>')}
for title in json.loads((ROOT/'backend/catalog.json').read_text(encoding='utf-8')):
    a,b,c,scene=scenes[title['id']]
    name=title['name'].upper()
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="640" height="400" viewBox="0 0 640 400"><defs><linearGradient id="sky" x2="0" y2="1"><stop stop-color="{a}"/><stop offset="1" stop-color="{b}"/></linearGradient><linearGradient id="shade" x2="0" y2="1"><stop stop-color="{c}" stop-opacity="0"/><stop offset="1" stop-color="{c}"/></linearGradient></defs><rect width="640" height="400" fill="url(#sky)"/>{scene}<rect width="640" height="400" fill="url(#shade)"/><text x="320" y="308" text-anchor="middle" fill="#f0eeda" font-family="Georgia,serif" font-size="{34 if len(name)>16 else 45}" letter-spacing="5">{name}</text><text x="320" y="340" text-anchor="middle" fill="#d0d4bf" font-family="Arial,sans-serif" font-size="9" letter-spacing="4">THE STREAMVAULT COLLECTION</text></svg>'
    (ROOT/'frontend/assets'/(title['id']+'.svg')).write_text(svg, encoding='utf-8')
