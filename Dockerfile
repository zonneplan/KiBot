FROM setsoft/kicad_auto:latest
LABEL AUTHOR Salvador E. Tropea <set@ieee.org>
LABEL Description="export various files from KiCad projects"

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

WORKDIR /mnt

ENTRYPOINT [ "/entrypoint.sh" ]
