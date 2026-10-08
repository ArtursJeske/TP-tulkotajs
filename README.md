# S+P datu lapu tulkotājs

Vietēja lietotne, kas S+P stiprinājumu datu lapas (PDF) pārvērš divvalodu failā:
**1. lappuse** ir angļu oriģināls, **2. lappuse** ir tā pati lapa latviski ar
nemainītu izkārtojumu, krāsām un skaitļiem.

Viss notiek uz tava datora. Faili netiek sūtīti uz internetu.

> **EN:** A small local Flask app that turns S+P fastener data sheets (PDF) into
> bilingual English + Latvian PDFs using an editable glossary. Numbers, codes and
> units are never translated. UI and docs are in Latvian.

## Kā tas strādā

1. No PDF tiek izvilkti teksta fragmenti, un katrs tiek klasificēts pēc fonta un
   krāsas: virsraksts, sekcija, lauka nosaukums vai vērtība.
2. Teksts tiek tulkots **tikai** pēc vārdnīcas `glossary.json`. Mašīntulkošana
   netiek izmantota, nekas netiek izdomāts.
3. Oriģinālais teksts 2. lappusē tiek pārklāts ar fona krāsu, un tulkojums tiek
   ierakstīts tajā pašā vietā ar DM Sans fontu. Ja latviskais teksts ir garāks,
   fonts tiek automātiski samazināts.
4. Ja kāds teksts nav vārdnīcā, tas paliek angliski un parādās saskarnē, kur to
   var iztulkot un uzreiz pārģenerēt failus.

## Uzstādīšana

Vajag **Python 3.10 vai jaunāku** ([python.org](https://www.python.org/downloads/);
uzstādot Windows vidē atzīmē "Add Python to PATH") un interneta savienojumu pirmajai
palaišanai.

```bash
git clone <repo-adrese>
cd <repo-mape>
```

Tad:

- **Windows:** divklikšķis uz `start.bat`
- **macOS / Linux:** `./start.sh`

Pirmajā reizē skripts uzstādīs bibliotēkas no `requirements.txt`, lejupielādēs
DM Sans fontu (`setup_fonts.py`) un atvērs pārlūku uz <http://127.0.0.1:5000>.
Turpmāk palaišana ir tas pats viens klikšķis. Apturēt var, aizverot termināļa
logu vai ar Ctrl+C.

<details>
<summary>Manuāla uzstādīšana (piem., virtuālajā vidē)</summary>

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python setup_fonts.py
python app.py
```

</details>

## Lietošana

1. Ievelc vienu vai vairākus PDF failus lodziņā (vai noklikšķini un izvēlies).
2. Katram failam parādās rinda ar lejupielādes saiti, un ir arī ZIP ar visiem.
3. Neatrastie teksti parādās sarakstā zem rezultātiem. Ieraksti latvisko
   tulkojumu un nospied **"Saglabāt un pārtaisīt"**: tulkojums tiek saglabāts
   vārdnīcā, un faili tiek uzģenerēti no jauna.

Gatavie faili tiek saglabāti mapē `out/`, augšupielādētie oriģināli mapē
`uploads/`. Abas mapes var brīvi iztukšot, un tās netiek iekļautas repozitorijā.

## Vārdnīca

`glossary.json` ir parasts JSON fails, ko var rediģēt arī ar roku vai caur
saskarni.

| Kategorija | Saturs | Piemērs |
|---|---|---|
| `labels` | Lauku nosaukumi ar kolu | `"Diameter (d):"` → `"Diametrs (d):"` |
| `sections` | Zilo joslu virsraksti | `"Technical data"` → `"Tehniskie dati"` |
| `product_types` | Produkta tips virsrakstā | `"Hexagon nuts"` → `"Seškanšu uzgriežņi"` |
| `values` | Teksta vērtības | `"Outer hex"` |
| `sentences` | Veselas rindkopas (6+ vārdi) | |
| `units` | Mērvienību aizvietojumi aiz skaitļa | `St.` → `gab.` |

## Kas nekad netiek tulkots

Skaitļi, izmēri, EAN/GTIN, artikulu numuri, materiālu apzīmējumi (A2, A4, 1.4301),
atslēgu izmēri (SW 17, TX20) un mērvienības tiek pārnesti burtiski. Par to atbild
`is_pure_data()` failā `sp_lib.py`. Tas ir apzināti: datu lapā kļūdaini pārrakstīts
izmērs ir daudz bīstamāks par netulkotu vārdu.

## Projekta struktūra

```
app.py            Flask serveris un API (/api/process, /api/rebuild, /api/glossary, /api/zip)
sp_lib.py         PDF apstrāde: teksta klasifikācija, tulkošana, pārrakstīšana
glossary.json     EN → LV vārdnīca
static/index.html Lietotāja saskarne
setup_fonts.py    Lejupielādē DM Sans un izveido Regular/Bold fontus
start.bat         Palaišana Windows vidē
start.sh          Palaišana macOS/Linux vidē
```

## Ierobežojumi un problēmu risināšana

**"python nav atrasts"**: Python nav uzstādīts vai nav pievienots PATH.

**Teksts pārklājas vai ir par mazu**: latviešu teksts parasti ir garāks par angļu,
un fonts tiek samazināts automātiski (līdz 5 pt). Ja tulkojums ir pārāk garš,
saīsini to vārdnīcā.

**Citas veidlapas datu lapa**: rīks ir pielāgots S+P datu lapu izkārtojumam. Ja
veidlapa mainās, teksts tiks atrasts, bet klasifikāciju vai līdzinājumu var nākties
pielāgot funkcijās `classify()` un `infer_alignment()` failā `sp_lib.py`.

**Skanēta datu lapa bez teksta slāņa**: netiek atbalstīta, jo nav teksta, ko izvilkt.
Tādām vispirms vajag OCR.

**Tiek apstrādāta tikai 1. lappuse**: daudzlapu PDF failiem tulkota tiek tikai
pirmā lappuse.

## Fonti

Lietotne izmanto [DM Sans](https://fonts.google.com/specimen/DM+Sans) fontu
(SIL Open Font License 1.1), ko `setup_fonts.py` lejupielādē no Google Fonts
repozitorija. Fontu faili repozitorijā netiek glabāti.
