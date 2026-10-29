"""Create a clearly synthetic ESX for installation tests, not validation."""
import argparse
import base64
from pathlib import Path
import zlib
import numpy as np
from lxml import etree


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():
        parser.error("Output exists; choose a new path")
    x=np.arange(18000,dtype=float)
    signal=np.full(18000,.01)
    for position,height,width in ((1000,150,8),(1320,80,8),(3000,50,15),(9300,65,18),(14500,30,12),(14750,70,16)):
        signal += height*np.exp(-.5*((x-position)/width)**2)
    encoded=base64.b64encode(zlib.compress(signal.astype(">f4").tobytes())).decode("ascii")
    root=etree.Element("SYNTHETIC_ESX",purpose="installation_test_only_not_real_biometry")
    for eye in ("OD","OS"):
        measurement=etree.SubElement(root,"MEASUREMENT",eye=eye)
        etree.SubElement(measurement,"START").text="2026.10.29"
        result=etree.SubElement(measurement,"BIOMETRYRESULT")
        etree.SubElement(result,"SCANDATA").text=encoded
        for element,position in ((0,1000),(1,1320)):
            cursor=etree.SubElement(result,"CURSOR")
            etree.SubElement(cursor,"CURSORELEMENT").text=str(element)
            etree.SubElement(cursor,"SCANPOS").text=str(position)
        for _ in range(5):
            scan=etree.SubElement(measurement,"ASCAN")
            for name,value in (("USED","true"),("SATURATED","false"),("SCANDATA",encoded)):
                etree.SubElement(scan,name).text=value
    args.output.parent.mkdir(parents=True,exist_ok=True)
    etree.ElementTree(root).write(str(args.output),encoding="utf-8",xml_declaration=True)
    print(args.output)


if __name__=="__main__":main()
