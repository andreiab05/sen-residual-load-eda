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

st.subheader(
    "Q1 - Cum arata sarcina reziduala pe parcursul zilei si cat ramane de acoperit?"
)

st.caption(
    "Selecteaza sursa sau sursele pe care vrei sa le scazi din consum pentru a vedea impactul lor asupra sarcinii ramase."
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

st.header("Q2 - Analiza rampelor")

st.write(
    "Analizam modificarile sarcinii reziduale intre observatii consecutive "
    "aflate la aproximativ 10 minute distanta."
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