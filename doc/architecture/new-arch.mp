input boxes
prologues := 3;
%outputformat := "svg";
outputtemplate := "%j-%c.eps";

defaultfont := "ptmr8r";
defaultscale := 2.0;

numeric u, w, h;
bound := 5;
u := 0.2cm;
w := 16u;
h := 9u;
hdist := 25u;
vdist := 20u;

vardef defaultboxsize(text bx) =
    bx.e = bx.w + (w, 0);
    bx.s = bx.n + (0, h);
enddef;

beginfig(1)
    pickup pencircle scaled 2pt;

    boxit.hla("HLA");
    boxit.opi("OPI");
    defaultboxsize(hla);
    defaultboxsize(opi);
    hla.c = (-hdist/2, 0);
    opi.c = (hdist/2, 0);
    drawboxed(hla, opi);
    
    boxit.ioc1("IOC");
    boxit.ioc2("IOC");
    boxit.vioc1("VIOC");
    boxit.vioc2("VIOC");
    defaultboxsize(ioc1);
    defaultboxsize(ioc2);
    defaultboxsize(vioc1);
    defaultboxsize(vioc2);
    ioc1.c = (-3*hdist/2, -vdist);
    ioc2.c = (-hdist/2, -vdist);
    vioc1.c = (hdist/2, -vdist);
    vioc2.c = (3*hdist/2, -vdist);
    drawboxed(ioc1, ioc2, vioc1, vioc2);

    boxit.hw1("HW");
    boxit.hw2("HW");
    defaultboxsize(hw1);
    defaultboxsize(hw2);
    hw1.s = ioc1.n;
    hw2.s = ioc2.n;
    drawboxed(hw1, hw2);

    boxit.va("VA");
    defaultboxsize(va);
    va.c = (hdist, -2*vdist);
    drawboxed(va);
    
    draw hla.n--(xpart hla.n, -vdist/2);
    draw opi.n--(xpart opi.n, -vdist/2);
    draw (-3*hdist/2, -vdist/2)--(3*hdist/2, -vdist/2);
    draw (xpart ioc1.s, -vdist/2)--ioc1.s;
    draw (xpart ioc2.s, -vdist/2)--ioc2.s;
    draw (xpart vioc1.s, -vdist/2)--vioc1.s;
    draw (xpart vioc2.s, -vdist/2)--vioc2.s;
    label.rt("Channel Access", (3*hdist/2, -vdist/2));

    numeric delta;
    yh := (ypart vioc1.n + ypart va.s)/2;
    draw vioc1.n--(xpart vioc1.n, yh);
    draw vioc2.n--(xpart vioc2.n, yh);
    draw (xpart vioc1.n, yh)--(xpart vioc2.n, yh);
    draw (xpart va.s, yh)--va.s;
    label.rt("Channel Access", (3*hdist/2, yh));
endfig;

end
