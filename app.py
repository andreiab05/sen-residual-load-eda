from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Configurarea aplicatiei

st.set_page_config(
    page_title="SEN 2025 - EDA",
    page_icon="⚡",
    layout="wide"
)


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Incarcarea si curatarea datelor

@st.cache_data
def load_data(file_name: Path) -> pd.DataFrame:
    df = pd.read_excel(file_name)

    df["Data"] = pd.to_datetime(
        df["Data"],
        dayfirst=True,
        errors="coerce"
    )

    numeric_columns = df.columns.drop("Data")

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    df = df.dropna(subset=["Data"])
    df = df.drop_duplicates()
    df = df.sort_values("Data").reset_index(drop=True)

    return df


DATA_FILE = Path(__file__).parent / "data" / "raw" / "Grafic_SEN_2025.xlsx"

if not DATA_FILE.exists():
    st.error(
        "Fisierul Grafic_SEN_2025.xlsx nu a fost gasit in data/raw/."
    )
    st.stop()

df = load_data(DATA_FILE)


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Coloanele necesare pentru Q1

df["RezidualaSolar[MW]"] = (
    df["Consum[MW]"]
    - df["Foto[MW]"]
)

df["RezidualaEolian[MW]"] = (
    df["Consum[MW]"]
    - df["Eolian[MW]"]
)

df["SarcinaReziduala[MW]"] = (
    df["Consum[MW]"]
    - df["Eolian[MW]"]
    - df["Foto[MW]"]
)

df["Ora"] = df["Data"].dt.hour


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Titlul si intrebarea analizata

st.title("Analiza Sistemului Energetic National - 2025")

st.header("Q1 - Sarcina reziduala")

st.caption(
    "Cum arata sarcina reziduala pe parcursul zilei si cat ramane de acoperit "
    "dupa contributia productiei eoliene si solare?"
)

st.write(
    "Selecteaza sursa sau sursele pentru a vedea separat impactul acestora "
    "asupra sarcinii ramase."
)


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Selectarea surselor

optiune = st.selectbox(
    "Sarcina ramasa dupa contributia:",
    [
        "Eolian + Solar",
        "Solar",
        "Eolian"
    ]
)

if optiune == "Solar":
    coloana_reziduala = "RezidualaSolar[MW]"
    label_reziduala = "Consum - Solar"

elif optiune == "Eolian":
    coloana_reziduala = "RezidualaEolian[MW]"
    label_reziduala = "Consum - Eolian"

else:
    coloana_reziduala = "SarcinaReziduala[MW]"
    label_reziduala = "Consum - Eolian - Solar"


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Profilul mediu pe fiecare ora a zilei

hourly_profile = df.groupby("Ora")[
    [
        "Consum[MW]",
        "RezidualaSolar[MW]",
        "RezidualaEolian[MW]",
        "SarcinaReziduala[MW]"
    ]
].mean()


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Indicatorii generali pentru selectia curenta

consumption_mean = df["Consum[MW]"].mean()
residual_mean = df[coloana_reziduala].mean()

residual_share = (
    df[coloana_reziduala].sum()
    / df["Consum[MW]"].sum() * 100
)

selected_sources_share = 100 - residual_share


col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Consum mediu",
    f"{consumption_mean:.0f} MW"
)

col2.metric(
    "Sarcina ramasa medie",
    f"{residual_mean:.0f} MW"
)

col3.metric(
    "Pondere ramasa",
    f"{residual_share:.1f}%"
)

col4.metric(
    f"Contributie {optiune.lower()}",
    f"{selected_sources_share:.1f}%"
)


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Grafic unic - consum vs sarcina ramasa pentru selectia curenta

st.subheader("Profilul mediu zilnic")

fig, ax = plt.subplots(figsize=(12, 6))

ax.plot(
    hourly_profile.index,
    hourly_profile["Consum[MW]"],
    marker="o",
    label="Consum mediu"
)

ax.plot(
    hourly_profile.index,
    hourly_profile[coloana_reziduala],
    marker="o",
    label=label_reziduala
)

ax.set_xlabel("Ora")
ax.set_ylabel("MW")
ax.set_title(
    f"Consum vs. sarcina ramasa - {optiune}"
)
ax.set_xticks(range(24))
ax.legend()
ax.grid(alpha=0.3)

st.pyplot(fig, use_container_width=True)

plt.close(fig)


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Momente relevante ale profilului zilnic

midday_profile = hourly_profile.loc[11:15]
evening_profile = hourly_profile.loc[17:21]

midday_min_hour = midday_profile[coloana_reziduala].idxmin()
midday_min_value = midday_profile[coloana_reziduala].min()

evening_max_hour = evening_profile[coloana_reziduala].idxmax()
evening_max_value = evening_profile[coloana_reziduala].max()


st.subheader("Momente relevante")

col1, col2 = st.columns(2)

col1.metric(
    "Minim mediu la pranz",
    f"{midday_min_value:.0f} MW"
)

col2.metric(
    "Maxim mediu seara",
    f"{evening_max_value:.0f} MW"
)

st.caption(
    f"Minimul mediu la pranz apare in jurul orei {midday_min_hour}:00, "
    f"iar maximul mediu de seara in jurul orei {evening_max_hour}:00."
)

# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Concluzie Q1 - calculata pentru Eolian + Solar

q1_residual_mean = df["SarcinaReziduala[MW]"].mean()

q1_residual_share = (
    df["SarcinaReziduala[MW]"].sum()
    / df["Consum[MW]"].sum() * 100
)

q1_wind_solar_share = 100 - q1_residual_share

q1_midday_profile = hourly_profile.loc[11:15]
q1_evening_profile = hourly_profile.loc[17:21]

q1_midday_min_hour = (
    q1_midday_profile["SarcinaReziduala[MW]"].idxmin()
)

q1_midday_min_value = (
    q1_midday_profile["SarcinaReziduala[MW]"].min()
)

q1_evening_max_hour = (
    q1_evening_profile["SarcinaReziduala[MW]"].idxmax()
)

q1_evening_max_value = (
    q1_evening_profile["SarcinaReziduala[MW]"].max()
)


st.subheader("Concluzie Q1")

st.markdown(
    f"""
Pe parcursul anului 2025, după scăderea producției **eoliene și solare** din consum,
sarcina reziduală medie este de aproximativ **{q1_residual_mean:.0f} MW**.
Aceasta reprezintă aproximativ **{q1_residual_share:.1f}% din consumul total**,
în timp ce eolianul și solarul acoperă împreună aproximativ
**{q1_wind_solar_share:.1f}%**.

Profilul mediu zilnic arată că sarcina reziduală scade în intervalul de prânz,
atingând un minim de aproximativ **{q1_midday_min_value:.0f} MW**
în jurul orei **{q1_midday_min_hour}:00**, iar spre seară crește până la
aproximativ **{q1_evening_max_value:.0f} MW**, în jurul orei
**{q1_evening_max_hour}:00**.

Prin urmare, chiar și după contribuția producției eoliene și solare,
**cea mai mare parte a consumului rămâne de acoperit de restul sistemului energetic**.
Graficul interactiv permite analizarea separată a impactului producției solare,
eoliene sau al celor două surse împreună asupra sarcinii rămase.
"""
)

# ==========================================================================================================================================================================
# Q2 - Care sunt cele mai mari rampe si la ce ore apar?

st.divider()

st.header("Q2 - Rampele sarcinii reziduale")

st.caption(
    "Care sunt cele mai mari rampe ale sarcinii reziduale si la ce ore apar?"
)

st.write(
    "Rampele sunt calculate intre observatii consecutive aflate la aproximativ "
    "10 minute distanta, astfel incat valorile sa fie comparabile."
)


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Calculul rampelor

df["IntervalMinute"] = (
    df["Data"].diff().dt.total_seconds() / 60
)

df["Rampa[MW]"] = (
    df["SarcinaReziduala[MW]"]
    - df["SarcinaReziduala[MW]"].shift(1)
)

# Pastram doar intervalele comparabile, de aproximativ 10 minute
df_rampe = df[
    (df["IntervalMinute"] >= 9)
    & (df["IntervalMinute"] <= 11)
].copy()


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Profilul mediu al rampelor pe ore

ramp_up = df_rampe[
    df_rampe["Rampa[MW]"] > 0
]

ramp_down = df_rampe[
    df_rampe["Rampa[MW]"] < 0
]

hourly_ramp_up = (
    ramp_up.groupby("Ora")["Rampa[MW]"].mean()
)

hourly_ramp_down = (
    ramp_down.groupby("Ora")["Rampa[MW]"].mean()
)


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Momente relevante ale profilului mediu

max_avg_ramp_up_hour = hourly_ramp_up.idxmax()
max_avg_ramp_up_value = hourly_ramp_up.max()

max_avg_ramp_down_hour = hourly_ramp_down.idxmin()
max_avg_ramp_down_value = hourly_ramp_down.min()


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Cele mai extreme rampe din 2025

largest_ramp_up = df_rampe.nlargest(
    10,
    "Rampa[MW]"
)

largest_ramp_down = df_rampe.nsmallest(
    10,
    "Rampa[MW]"
)

max_ramp_up = largest_ramp_up.iloc[0]
max_ramp_down = largest_ramp_down.iloc[0]


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Indicatori principali

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Cel mai puternic ramp-up mediu",
    f"{max_avg_ramp_up_value:.0f} MW / ~10 min",
    help=f"In jurul orei {max_avg_ramp_up_hour}:00"
)

col2.metric(
    "Cel mai puternic ramp-down mediu",
    f"{max_avg_ramp_down_value:.0f} MW / ~10 min",
    help=f"In jurul orei {max_avg_ramp_down_hour}:00"
)

col3.metric(
    "Ramp-up maxim in 2025",
    f"+{max_ramp_up['Rampa[MW]']:.0f} MW",
    help=max_ramp_up["Data"].strftime("%d.%m.%Y %H:%M")
)

col4.metric(
    "Ramp-down maxim in 2025",
    f"{max_ramp_down['Rampa[MW]']:.0f} MW",
    help=max_ramp_down["Data"].strftime("%d.%m.%Y %H:%M")
)

# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Grafic 1 - Profilul mediu zilnic al rampelor

st.subheader("Profilul mediu zilnic al rampelor")

fig, ax = plt.subplots(figsize=(12, 6))

ax.plot(
    hourly_ramp_up.index,
    hourly_ramp_up.values,
    marker="o",
    label="Ramp-up mediu"
)

ax.plot(
    hourly_ramp_down.index,
    hourly_ramp_down.values,
    marker="o",
    label="Ramp-down mediu"
)

ax.axhline(0)

ax.set_xlabel("Ora")
ax.set_ylabel("Rampa [MW / ~10 min]")
ax.set_title(
    "Profilul mediu zilnic al rampelor sarcinii reziduale"
)

ax.set_xticks(range(24))
ax.legend()
ax.grid(alpha=0.3)

st.pyplot(
    fig,
    use_container_width=True
)

plt.close(fig)


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Grafic 2 - Cele mai extreme rampe observate in 2025

st.subheader("Cele mai extreme rampe din 2025")

top_ramps = pd.concat([
    largest_ramp_down,
    largest_ramp_up
]).sort_values("Rampa[MW]")

fig, ax = plt.subplots(figsize=(12, 6))

ax.bar(
    top_ramps["Data"].dt.strftime("%d-%m %H:%M"),
    top_ramps["Rampa[MW]"]
)

ax.axhline(0)

ax.set_xlabel("Data si ora")
ax.set_ylabel("Rampa [MW / ~10 min]")
ax.set_title(
    "Cele mai mari rampe ale sarcinii reziduale in 2025"
)

ax.tick_params(
    axis="x",
    rotation=70
)

ax.grid(
    axis="y",
    alpha=0.3
)

fig.tight_layout()

st.pyplot(
    fig,
    use_container_width=True
)

plt.close(fig)


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Top 10 rampe - detalii

with st.expander("Vezi top 10 ramp-up si ramp-down"):
    col1, col2 = st.columns(2)

    with col1:
        st.write("**Top 10 ramp-up**")

        st.dataframe(
            largest_ramp_up[
                [
                    "Data",
                    "Ora",
                    "Rampa[MW]"
                ]
            ],
            hide_index=True
        )

    with col2:
        st.write("**Top 10 ramp-down**")

        st.dataframe(
            largest_ramp_down[
                [
                    "Data",
                    "Ora",
                    "Rampa[MW]"
                ]
            ],
            hide_index=True
        )


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Concluzie Q2

st.subheader("Concluzie Q2")

st.markdown(
    f"""
Profilul mediu zilnic arata ca cele mai puternice **cresteri ale sarcinii reziduale**
apar in jurul orei **{max_avg_ramp_up_hour}:00**, cu un ramp-up mediu de aproximativ
**{max_avg_ramp_up_value:.0f} MW intr-un interval de aproximativ 10 minute**.

Cele mai accentuate scaderi medii apar in jurul orei
**{max_avg_ramp_down_hour}:00**, cu un ramp-down mediu de aproximativ
**{max_avg_ramp_down_value:.0f} MW / ~10 min**.

La nivelul observatiilor individuale din 2025, cea mai mare crestere a fost de
aproximativ **+{max_ramp_up['Rampa[MW]']:.0f} MW / ~10 min**, inregistrata la
**{max_ramp_up['Data'].strftime('%d.%m.%Y %H:%M')}**, iar cea mai mare scadere
a fost de aproximativ **{max_ramp_down['Rampa[MW]']:.0f} MW / ~10 min**,
inregistrata la **{max_ramp_down['Data'].strftime('%d.%m.%Y %H:%M')}**.

Rezultatele indica faptul ca sarcina reziduala prezinta variatii rapide pe
intervale scurte, iar intervalul orar identificat pentru cel mai puternic
ramp-up mediu necesita o crestere mai rapida a productiei sau a altor resurse
de echilibrare pentru a acoperi modificarea sarcinii reziduale.
"""
)

# ==========================================================================================================================================================================
# Q3 - Exista momente cu duck curve?

st.divider()

st.header("Q3 - Efectul de duck curve")

st.caption(
    "Exista momente cu scadere a sarcinii reziduale la pranz, asociata productiei solare, "
    "urmata de o crestere puternica spre seara?"
)

st.write(
    "Analiza este realizata separat pentru fiecare anotimp, folosind profilurile medii "
    "orare ale consumului, productiei solare si sarcinii reziduale."
)


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Impartirea datelor pe anotimpuri

df["Anotimp"] = df["Data"].dt.month.map({
    12: "Iarna",
    1: "Iarna",
    2: "Iarna",
    3: "Primavara",
    4: "Primavara",
    5: "Primavara",
    6: "Vara",
    7: "Vara",
    8: "Vara",
    9: "Toamna",
    10: "Toamna",
    11: "Toamna"
})

sezoane = [
    "Iarna",
    "Primavara",
    "Vara",
    "Toamna"
]


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Profilul mediu pe ore pentru fiecare anotimp

hourly_duck = df.groupby(
    ["Anotimp", "Ora"]
)[
    [
        "Consum[MW]",
        "Foto[MW]",
        "SarcinaReziduala[MW]"
    ]
].mean()


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Calcularea indicatorilor pentru fiecare anotimp

duck_results = []

for sezon in sezoane:

    sezon_data = hourly_duck.loc[sezon]

    morning_profile = sezon_data.loc[6:10]
    midday_profile = sezon_data.loc[11:15]
    evening_profile = sezon_data.loc[17:21]

    # Peak solar
    solar_peak_hour = sezon_data["Foto[MW]"].idxmax()
    solar_peak_value = sezon_data["Foto[MW]"].max()

    # Minim rezidual la pranz
    midday_min_hour = (
        midday_profile["SarcinaReziduala[MW]"].idxmin()
    )

    midday_min_value = (
        midday_profile["SarcinaReziduala[MW]"].min()
    )

    # Nivel ridicat dimineata
    morning_max_hour = (
        morning_profile["SarcinaReziduala[MW]"].idxmax()
    )

    morning_max_value = (
        morning_profile["SarcinaReziduala[MW]"].max()
    )

    midday_drop = (
        morning_max_value
        - midday_min_value
    )

    # Maxim rezidual seara
    evening_max_hour = (
        evening_profile["SarcinaReziduala[MW]"].idxmax()
    )

    evening_max_value = (
        evening_profile["SarcinaReziduala[MW]"].max()
    )

    evening_rise = (
        evening_max_value
        - midday_min_value
    )

    # Cea mai mare crestere intre doua ore consecutive spre seara
    evening_hourly_change = (
        sezon_data.loc[16:21, "SarcinaReziduala[MW]"].diff()
    )

    max_evening_rise_hour = (
        evening_hourly_change.idxmax()
    )

    max_evening_rise_value = (
        evening_hourly_change.max()
    )

    duck_results.append({
        "Anotimp": sezon,
        "Ora peak solar": solar_peak_hour,
        "Peak solar [MW]": solar_peak_value,
        "Ora minim rezidual": midday_min_hour,
        "Minim rezidual [MW]": midday_min_value,
        "Scadere dimineata-pranz [MW]": midday_drop,
        "Ora maxim seara": evening_max_hour,
        "Maxim rezidual seara [MW]": evening_max_value,
        "Crestere pranz-seara [MW]": evening_rise,
        "Ora crestere maxima seara": max_evening_rise_hour,
        "Crestere maxima orara [MW]": max_evening_rise_value
    })


duck_summary = pd.DataFrame(duck_results)


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Selectarea anotimpului

sezon_selectat = st.selectbox(
    "Selecteaza anotimpul:",
    sezoane,
    key="duck_season"
)

sezon_data = hourly_duck.loc[sezon_selectat]

rezultat_sezon = duck_summary[
    duck_summary["Anotimp"] == sezon_selectat
].iloc[0]


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Indicatori principali

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Peak solar",
    f"{rezultat_sezon['Peak solar [MW]']:.0f} MW",
    help=f"In jurul orei {int(rezultat_sezon['Ora peak solar'])}:00"
)

col2.metric(
    "Minim rezidual la pranz",
    f"{rezultat_sezon['Minim rezidual [MW]']:.0f} MW",
    help=f"In jurul orei {int(rezultat_sezon['Ora minim rezidual'])}:00"
)

col3.metric(
    "Scadere dimineata - pranz",
    f"{rezultat_sezon['Scadere dimineata-pranz [MW]']:.0f} MW"
)

col4.metric(
    "Crestere pranz - seara",
    f"+{rezultat_sezon['Crestere pranz-seara [MW]']:.0f} MW"
)


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Grafic - profil sezonier

st.subheader(f"Profil mediu zilnic - {sezon_selectat}")

fig, ax = plt.subplots(figsize=(12, 6))

ax.plot(
    sezon_data.index,
    sezon_data["Consum[MW]"],
    marker="o",
    label="Consum mediu"
)

ax.plot(
    sezon_data.index,
    sezon_data["SarcinaReziduala[MW]"],
    marker="o",
    label="Sarcina reziduala"
)

ax.plot(
    sezon_data.index,
    sezon_data["Foto[MW]"],
    marker="o",
    label="Productie solara medie"
)

ax.set_xlabel("Ora")
ax.set_ylabel("MW")

ax.set_title(
    f"Consum, productie solara si sarcina reziduala - {sezon_selectat}"
)

ax.set_xticks(range(24))
ax.legend()
ax.grid(alpha=0.3)

st.pyplot(
    fig,
    use_container_width=True
)

plt.close(fig)


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Detalii despre profilul selectat

st.subheader("Momente relevante")

col1, col2 = st.columns(2)

col1.metric(
    "Maxim rezidual seara",
    f"{rezultat_sezon['Maxim rezidual seara [MW]']:.0f} MW",
    help=f"In jurul orei {int(rezultat_sezon['Ora maxim seara'])}:00"
)

col2.metric(
    "Cea mai mare crestere orara spre seara",
    f"+{rezultat_sezon['Crestere maxima orara [MW]']:.0f} MW",
    help=(
        f"Cresterea este observata la trecerea spre ora "
        f"{int(rezultat_sezon['Ora crestere maxima seara'])}:00"
    )
)


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Comparatie intre anotimpuri

with st.expander("Vezi comparatia intre anotimpuri"):

    st.dataframe(
        duck_summary[
            [
                "Anotimp",
                "Ora peak solar",
                "Peak solar [MW]",
                "Ora minim rezidual",
                "Minim rezidual [MW]",
                "Scadere dimineata-pranz [MW]",
                "Crestere pranz-seara [MW]",
                "Crestere maxima orara [MW]"
            ]
        ].round(0),
        hide_index=True,
        use_container_width=True
    )


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Concluzie Q3

st.subheader("Concluzie Q3")

st.markdown(
    f"""
In **{sezon_selectat.lower()}**, productia solara atinge valoarea maxima de aproximativ
**{rezultat_sezon['Peak solar [MW]']:.0f} MW** in jurul orei
**{int(rezultat_sezon['Ora peak solar'])}:00**.

In intervalul de pranz, sarcina reziduala ajunge la un minim de aproximativ
**{rezultat_sezon['Minim rezidual [MW]']:.0f} MW**, in jurul orei
**{int(rezultat_sezon['Ora minim rezidual'])}:00**. Fata de nivelul ridicat din
intervalul de dimineata, aceasta reprezinta o scadere de aproximativ
**{rezultat_sezon['Scadere dimineata-pranz [MW]']:.0f} MW**.

Spre seara, pe masura ce productia solara se reduce, sarcina reziduala creste pana la
aproximativ **{rezultat_sezon['Maxim rezidual seara [MW]']:.0f} MW**, ceea ce
reprezinta o crestere de aproximativ
**{rezultat_sezon['Crestere pranz-seara [MW]']:.0f} MW** fata de minimul de la pranz.

Acest profil este **compatibil cu fenomenul de duck curve**: cresterea productiei
solare coincide cu reducerea sarcinii reziduale in jurul pranzului, iar reducerea
productiei solare spre seara este insotita de o crestere puternica a sarcinii
reziduale. Analiza rampelor din Q2 completeaza aceasta observatie prin evidentierea
vitezei cu care sarcina reziduala se poate modifica in intervalele scurte de timp.
"""
)

# ==========================================================================================================================================================================
# Q4 - Cat de bine urmareste productia totala consumul?

st.divider()

st.header("Q4 - Productie, consum si sold")

st.caption(
    "Cat de bine urmareste productia totala consumul si exista decalaje "
    "sistematice de subproductie sau supraproductie?"
)

st.write(
    "Analizam diferenta dintre productia interna si consum, iar apoi verificam "
    "in ce masura aceasta diferenta este compensata prin soldul de import/export."
)


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Diferenta dintre productie si consum

df["DiferentaProductieConsum[MW]"] = (
    df["Productie[MW]"]
    - df["Consum[MW]"]
)

df["EroareBalanta[MW]"] = (
    df["Productie[MW]"]
    + df["Sold[MW]"]
    - df["Consum[MW]"]
)


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Profilul mediu pe ore

hourly_balance = df.groupby("Ora")[
    [
        "Productie[MW]",
        "Consum[MW]",
        "Sold[MW]",
        "DiferentaProductieConsum[MW]",
        "EroareBalanta[MW]"
    ]
].mean()


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Indicatorii generali

mean_difference = (
    df["DiferentaProductieConsum[MW]"].mean()
)

median_difference = (
    df["DiferentaProductieConsum[MW]"].median()
)

deficit_share = (
    (df["DiferentaProductieConsum[MW]"] < 0).mean()
    * 100
)

surplus_share = (
    (df["DiferentaProductieConsum[MW]"] > 0).mean()
    * 100
)

mean_sold = df["Sold[MW]"].mean()

mean_abs_balance_error = (
    df["EroareBalanta[MW]"].abs().mean()
)

mean_consumption = df["Consum[MW]"].mean()

balance_error_share = (
    mean_abs_balance_error
    / mean_consumption
    * 100
)


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Momente relevante ale profilului zilnic

max_avg_deficit_hour = (
    hourly_balance["DiferentaProductieConsum[MW]"].idxmin()
)

max_avg_deficit_value = (
    hourly_balance["DiferentaProductieConsum[MW]"].min()
)

max_avg_surplus_hour = (
    hourly_balance["DiferentaProductieConsum[MW]"].idxmax()
)

max_avg_surplus_value = (
    hourly_balance["DiferentaProductieConsum[MW]"].max()
)


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Extremele individuale

largest_deficits = df.nsmallest(
    10,
    "DiferentaProductieConsum[MW]"
)

largest_surpluses = df.nlargest(
    10,
    "DiferentaProductieConsum[MW]"
)


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Indicatori principali

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Diferenta medie productie - consum",
    f"{mean_difference:.0f} MW"
)

col2.metric(
    "Productie sub consum",
    f"{deficit_share:.1f}%"
)

col3.metric(
    "Sold mediu",
    f"{mean_sold:.0f} MW"
)

col4.metric(
    "Eroare medie a balantei",
    f"{mean_abs_balance_error:.2f} MW",
    help=f"{balance_error_share:.3f}% din consumul mediu"
)


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Grafic 1 - Productie vs consum

st.subheader("Profilul mediu zilnic")

fig, ax = plt.subplots(figsize=(12, 6))

ax.plot(
    hourly_balance.index,
    hourly_balance["Consum[MW]"],
    marker="o",
    label="Consum mediu"
)

ax.plot(
    hourly_balance.index,
    hourly_balance["Productie[MW]"],
    marker="o",
    label="Productie medie"
)

ax.set_xlabel("Ora")
ax.set_ylabel("MW")

ax.set_title(
    "Profil mediu zilnic al productiei si consumului"
)

ax.set_xticks(range(24))
ax.legend()
ax.grid(alpha=0.3)

st.pyplot(
    fig,
    use_container_width=True
)

plt.close(fig)


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Grafic 2 - Diferenta productie - consum

st.subheader("Decalajul mediu dintre productie si consum")

fig, ax = plt.subplots(figsize=(12, 6))

ax.plot(
    hourly_balance.index,
    hourly_balance["DiferentaProductieConsum[MW]"],
    marker="o",
    label="Productie - Consum"
)

ax.axhline(0)

ax.set_xlabel("Ora")
ax.set_ylabel("MW")

ax.set_title(
    "Diferenta medie dintre productie si consum pe ore"
)

ax.set_xticks(range(24))
ax.legend()
ax.grid(alpha=0.3)

st.pyplot(
    fig,
    use_container_width=True
)

plt.close(fig)


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Momente relevante

st.subheader("Momente relevante")

col1, col2 = st.columns(2)

col1.metric(
    "Cel mai mare deficit mediu",
    f"{max_avg_deficit_value:.0f} MW",
    help=f"In jurul orei {max_avg_deficit_hour}:00"
)

col2.metric(
    "Cel mai mare surplus mediu",
    f"+{max_avg_surplus_value:.0f} MW",
    help=f"In jurul orei {max_avg_surplus_hour}:00"
)


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Grafic 3 - Verificarea balantei energetice

st.subheader("Verificarea balantei energetice")

st.caption(
    "Daca productia si soldul compenseaza consumul, valoarea "
    "Productie + Sold - Consum trebuie sa ramana apropiata de zero."
)

fig, ax = plt.subplots(figsize=(12, 6))

ax.plot(
    hourly_balance.index,
    hourly_balance["EroareBalanta[MW]"],
    marker="o",
    label="Productie + Sold - Consum"
)

ax.axhline(0)

ax.set_xlabel("Ora")
ax.set_ylabel("MW")

ax.set_title(
    "Eroarea medie a balantei energetice pe ore"
)

ax.set_xticks(range(24))
ax.legend()
ax.grid(alpha=0.3)

st.pyplot(
    fig,
    use_container_width=True
)

plt.close(fig)


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Extreme individuale

with st.expander("Vezi top 10 deficit si surplus"):

    col1, col2 = st.columns(2)

    with col1:

        st.write("**Top 10 momente cu productie sub consum**")

        st.dataframe(
            largest_deficits[
                [
                    "Data",
                    "Productie[MW]",
                    "Consum[MW]",
                    "DiferentaProductieConsum[MW]",
                    "Sold[MW]"
                ]
            ],
            hide_index=True,
            use_container_width=True
        )

    with col2:

        st.write("**Top 10 momente cu productie peste consum**")

        st.dataframe(
            largest_surpluses[
                [
                    "Data",
                    "Productie[MW]",
                    "Consum[MW]",
                    "DiferentaProductieConsum[MW]",
                    "Sold[MW]"
                ]
            ],
            hide_index=True,
            use_container_width=True
        )


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Concluzie Q4

st.subheader("Concluzie Q4")

st.markdown(
    f"""
Productia interna prezinta un **decalaj sistematic spre deficit fata de consum**.
In 2025, productia a fost in medie cu aproximativ
**{abs(mean_difference):.0f} MW sub consum**, iar in
**{deficit_share:.1f}% dintre observatii** productia a fost mai mica decat consumul.

Deficitul este mai pronuntat spre seara, atingand in profilul mediu aproximativ
**{max_avg_deficit_value:.0f} MW** in jurul orei
**{max_avg_deficit_hour}:00**. In jurul pranzului apar si perioade cu surplus,
cel mai mare surplus mediu fiind de aproximativ
**+{max_avg_surplus_value:.0f} MW** la ora **{max_avg_surplus_hour}:00**.

Diferenta dintre productie si consum este insa compensata aproape integral prin
soldul de import/export. Soldul mediu este de aproximativ
**{mean_sold:.0f} MW**, foarte apropiat ca valoare de deficitul mediu de productie.

Dupa includerea soldului, relatia **Productie + Sold ≈ Consum** prezinta o eroare
medie absoluta de doar **{mean_abs_balance_error:.2f} MW**, adica aproximativ
**{balance_error_share:.3f}% din consumul mediu**.

Prin urmare, exista un decalaj sistematic intre productia interna si consum,
predominant spre subproductie, dar **nu se observa un dezechilibru semnificativ
al balantei sistemului**, deoarece diferenta este compensata aproape complet
prin schimburile de energie reflectate de sold.
"""
)