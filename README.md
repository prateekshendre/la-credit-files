# LA Credit Files

A weekly, data-first look at the credit managers of Los Angeles, built only from public SEC filings.
Each episode ships as a LinkedIn carousel plus the data and code behind it, so every number can be checked.

By Prateek Shendre. Over four years in structured credit risk and analytics at TCW in downtown LA. New episode every Tuesday on [LinkedIn](https://www.linkedin.com/in/prateek-shendre).

## Episodes

| # | Title | Data | Status |
|---|-------|------|--------|
| 01 | LA runs more credit than you think | SEC Form ADV (registered adviser roster, Nov 2026) | Published Nov 17, 2026 |
| 02 | Inside Ares Capital's loan book | ARCC Form 10-Q, Sep 30, 2026 | Published Nov 24, 2026 |
| 03 | Same loan, different price across BDCs | BDC schedules of investments | Planned |

## Episode 02 at a glance

- Ares Capital (ARCC) holds **$29.2B** at fair value across **636** companies (1,422 line items in the Schedule of Investments).
- 58% first lien loans; about 28% of the book is equity (preferred, Ivy Hill and other equity).
- Software and Services is the largest industry at 21.6% (23.8% in Dec 2025); 5 of the 8 biggest markdowns vs cost are software businesses.
- Non-accruals rose from 1.8% to 2.4% of cost; grades 1 and 2 rose from 3.8% to 5.8% of fair value; PIK was 16.4% of Q3 income.
- Of every $100 of Q3 investment income: $29 to lenders, $25 to Ares in fees, $3 admin and tax, $43 net investment income.

Data: `e02/data/arcc_q3_2026.json` (fields marked `parsed` are computed from the Schedule of Investments; the rest are as reported). Build: `python3 e02/build.py`.

## Episode 01 at a glance

- 12 credit-first firms with main offices in LA, Orange and Ventura counties manage **$5.16T** in regulatory AUM.
- PIMCO is about 71% of that. The other 11 add up to **$1.50T**.
- The Westside (Century City, West LA, Santa Monica, Marina del Rey) holds **$751B**; two Bunker Hill buildings hold **$540B**.
- Bond houses run mostly mutual funds and separate accounts; the newer shops run mostly private funds.

## Method (Episode 01)

- Source: SEC "Information About Registered Investment Advisers" roster, November 2026 file
  (`ia110226-registered.zip`), which reprints Form ADV Part 1A fields for every SEC-registered adviser.
- Fields used: Item 5.F(2)(c) total regulatory AUM, 5.F(2)(a) discretionary, 5.A and 5.B(1) staff,
  5.D(d)(3), 5.D(e)(3) and 5.D(f)(3) AUM for registered funds, BDCs and pooled vehicles, main office address.
- Firm set: hand-picked advisers whose business is mainly credit, with a main office in LA, Orange or Ventura county.
  Affiliated advisers are summed into one group (Ares: 4 entities, TCW: 3 including MetWest).
  Ares figures include its private equity and real estate businesses.
- Regulatory AUM is gross, as filed, and dated to each firm's latest annual update, so dates differ by firm.
  Summing affiliated advisers can double count sub-advised assets.
- Nothing here is investment advice.

## Run it

```bash
pip install pandas playwright
python3 e01/build.py      # writes e01/out/*.png and LA_Credit_Files_E01.pdf
```

## Layout

```
data/e01_form_adv_la_credit.csv   raw fields per adviser, as filed
e01/build.py                      stats, charts and carousel
e01/out/                          slides (PNG) and the carousel PDF
```
