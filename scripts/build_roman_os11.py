"""Extract a browser-sized real Roman CGI OS11 product from the official v3 archive."""
from __future__ import annotations
from datetime import datetime,timezone
import hashlib,json,zipfile
from pathlib import Path
import numpy as np,requests
from astropy.io import fits
from PIL import Image

URL="https://roman.ipac.caltech.edu/data/sims/coronagraph/os11/hlc_os11_v3.zip"
EXPECTED=448_088_109
def digest(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for c in iter(lambda:f.read(1024*1024),b""):h.update(c)
 return h.hexdigest()
def main():
 cache=Path("data/hlc_os11_v3.zip");cache.parent.mkdir(exist_ok=True)
 if not cache.exists() or cache.stat().st_size!=EXPECTED:
  part=cache.with_suffix(".part")
  with requests.get(URL,stream=True,timeout=180) as r:
   r.raise_for_status()
   with part.open("wb") as f:
    for c in r.iter_content(1024*1024):f.write(c)
  if part.stat().st_size!=EXPECTED:raise ValueError(part.stat().st_size)
  part.replace(cache)
 with zipfile.ZipFile(cache) as z:
  names=z.namelist(); candidates=[n for n in names if "sky_transmission" in n.lower() and n.lower().endswith(".fits")]
  if not candidates:
   print("\n".join(n for n in names if n.lower().endswith(".fits") )[:20000]);raise ValueError("sky transmission map not found")
  member=candidates[0]; raw=z.read(member)
 with fits.open(__import__('io').BytesIO(raw)) as hdul:data=np.squeeze(np.asarray(hdul[0].data,dtype=float));header={k:str(v) for k,v in hdul[0].header.items() if k in {"NAXIS1","NAXIS2","BUNIT","XCENTER","YCENTER","PIXSCALE","COMMENT"}}
 finite=np.isfinite(data);lo,hi=np.nanpercentile(data[finite],[1,99]);scaled=np.clip((data-lo)/(hi-lo),0,1);img=Image.fromarray(np.uint8(scaled*255)).resize((512,512),Image.Resampling.LANCZOS);outdir=Path("public/data");outdir.mkdir(parents=True,exist_ok=True);img.save(outdir/"roman-hlc-sky-transmission.webp",quality=90)
 step=max(1,data.shape[0]//128);thumb=data[::step,::step][:128,:128]
 payload={"schema":"coronagraph.roman-os11/1","generatedAtUtc":datetime.now(timezone.utc).isoformat(),"source":{"url":URL,"expectedBytes":EXPECTED,"sha256":digest(cache),"member":member,"memberSha256":hashlib.sha256(raw).hexdigest(),"archivePage":"https://roman.ipac.caltech.edu/page/coronagraph-public-images-html","credit":"Roman CGI instrument team / JPL / IPAC"},"fits":{"shape":list(data.shape),"header":header,"minimum":float(np.nanmin(data)),"maximum":float(np.nanmax(data)),"median":float(np.nanmedian(data))},"preview":"data/roman-hlc-sky-transmission.webp","grid":np.round(thumb,6).tolist(),"warning":"OS11 is a simulated observing scenario, not on-sky Roman data. The sky-transmission map measures off-axis PSF peak throughput, not achieved contrast or planet detectability."}
 (outdir/"roman-hlc-os11.json").write_text(json.dumps(payload,separators=(",",":")),encoding="utf-8");print(json.dumps({"member":member,"shape":data.shape,"hash":payload["source"]["sha256"]},indent=2))
if __name__=="__main__":main()
