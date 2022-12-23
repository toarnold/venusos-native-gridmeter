#!/bin/bash
TARGETDIR=/data/venus_gridmeter/
STARTCMD=start_gridmeter
mkdir -p ${TARGETDIR}
cp -v ./launchService.py ${TARGETDIR}
chmod +x ${TARGETDIR}launchService.py
cp -v ./DBusNativeGridMeterService.py ${TARGETDIR}
cp -v ./config.json ${TARGETDIR}
cp -v ./${STARTCMD} ${TARGETDIR}
chmod +x ${TARGETDIR}${STARTCMD}
ln -s /opt/victronenergy/dbus-pump/ext/velib_python ${TARGETDIR}
RCLOCAL=/data/rc.local
if [ -f "${RCLOCAL}" ]; then
    if grep -q "&& ./${STARTCMD}" "${RCLOCAL}"; then
        echo "${RCLOCAL} is correct"
    else
        echo "extend ${RCLOCAL}"
        echo "cd ${TARGETDIR} && ./${STARTCMD}" >> ${RCLOCAL}
    fi
else
    echo "create ${RCLOCAL}"
    echo -e '#!/bin/bash' >> ${RCLOCAL}
    echo "cd ${TARGETDIR} && ./${STARTCMD}" >> ${RCLOCAL}
    chmod +x ${RCLOCAL}
fi
