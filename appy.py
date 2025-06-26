import streamlit as st
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="GFS Spatial Viewer")

# ==========================
# Fungsi Load Dataset
# ==========================

@st.cache_data
def load_dataset(run_date, run_hour):
    base_url = f"https://nomads.ncep.noaa.gov:9090/dods/gfs_0p25_1hr/gfs{run_date}/gfs_0p25_1hr_{run_hour}z"
    ds = xr.open_dataset(base_url)
    return ds

# ==========================
# Sidebar - Input Parameter
# ==========================

st.sidebar.title("GFS Spatial Data Viewer")

# Pilihan tanggal dan jam run GFS
today = datetime.utcnow()
run_date = st.sidebar.date_input("GFS Run Date (UTC)", today.date())
run_hour = st.sidebar.selectbox("GFS Run Hour (UTC)", ["00", "06", "12", "18"])

# Pilihan parameter
param = st.sidebar.selectbox(
    "Parameter",
    {
        "Curah Hujan per jam (prate)": "prate",
        "Suhu Permukaan (tmp2m)": "tmp2m",
        "Angin Permukaan (ugrd10m & vgrd10m)": "wind",
        "Tekanan Permukaan Laut (prmsl)": "prmsl"
    }.keys()
)

# Forecast hour
forecast_hour = st.sidebar.slider("Forecast Hour (jam ke depan)", 0, 240, 0, step=1)

# Batas peta
lat_min = st.sidebar.number_input("Lat Min", -90.0, 90.0, -15.0)
lat_max = st.sidebar.number_input("Lat Max", -90.0, 90.0, 15.0)
lon_min = st.sidebar.number_input("Lon Min", 0.0, 360.0, 90.0)
lon_max = st.sidebar.number_input("Lon Max", 0.0, 360.0, 150.0)

# ==========================
# Load Dataset
# ==========================
try:
    st.info(f"Loading data from GFS {run_date} {run_hour}z...")
    ds = load_dataset(run_date.strftime("%Y%m%d"), run_hour)
except Exception as e:
    st.error(f"Error loading dataset: {e}")
    st.stop()

# ==========================
# Ekstrak dan Visualisasi
# ==========================

def plot_map(data, lats, lons, title, cmap='viridis'):
    fig = plt.figure(figsize=(10,6))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.set_extent([lon_min, lon_max, lat_min, lat_max])
    mesh = ax.pcolormesh(lons, lats, data, transform=ccrs.PlateCarree(), cmap=cmap)
    ax.coastlines()
    ax.add_feature(cfeature.BORDERS, linestyle=':')
    ax.gridlines(draw_labels=True)
    plt.colorbar(mesh, orientation='horizontal', pad=0.05, label=title)
    plt.title(title)
    st.pyplot(fig)

if param == "Curah Hujan per jam (prate)":
    try:
        var = ds['prate'][forecast_hour, :, :] * 3600  # Konversi ke mm/jam
        lats = ds['lat'].values
        lons = ds['lon'].values
        subset = var.sel(lat=slice(lat_max, lat_min), lon=slice(lon_min, lon_max))
        plot_map(subset.values, subset['lat'].values, subset['lon'].values, "Curah Hujan (mm/jam)", cmap='Blues')
    except Exception as e:
        st.error(f"Gagal memuat data curah hujan: {e}")

elif param == "Suhu Permukaan (tmp2m)":
    try:
        var = ds['tmp2m'][forecast_hour, :, :] - 273.15  # Kelvin ke Celsius
        lats = ds['lat'].values
        lons = ds['lon'].values
        subset = var.sel(lat=slice(lat_max, lat_min), lon=slice(lon_min, lon_max))
        plot_map(subset.values, subset['lat'].values, subset['lon'].values, "Suhu (°C)", cmap='coolwarm')
    except Exception as e:
        st.error(f"Gagal memuat data suhu: {e}")

elif param == "Angin Permukaan (ugrd10m & vgrd10m)":
    try:
        u = ds['ugrd10m'][forecast_hour, :, :]
        v = ds['vgrd10m'][forecast_hour, :, :]
        wind_speed = np.sqrt(u**2 + v**2)
        lats = ds['lat'].values
        lons = ds['lon'].values
        subset = wind_speed.sel(lat=slice(lat_max, lat_min), lon=slice(lon_min, lon_max))
        plot_map(subset.values, subset['lat'].values, subset['lon'].values, "Kecepatan Angin (m/s)", cmap='plasma')
    except Exception as e:
        st.error(f"Gagal memuat data angin: {e}")

elif param == "Tekanan Permukaan Laut (prmsl)":
    try:
        var = ds['prmsl'][forecast_hour, :, :] / 100  # Pa ke hPa
        lats = ds['lat'].values
        lons = ds['lon'].values
        subset = var.sel(lat=slice(lat_max, lat_min), lon=slice(lon_min, lon_max))
        plot_map(subset.values, subset['lat'].values, subset['lon'].values, "Tekanan Permukaan Laut (hPa)", cmap='YlGnBu')
    except Exception as e:
        st.error(f"Gagal memuat data tekanan: {e}")

else:
    st.warning("Parameter belum dipilih atau tidak dikenali.")

