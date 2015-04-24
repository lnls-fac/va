input boxes
prologues := 3;
outputtemplate := "%j-%c.eps";

numeric u, w, h;
u := 0.1cm;
w := 16u;
h := 9u;
hdist := 25u;
vdist := 20u;

vardef defaultboxsize(text bx) =
    bx.e = bx.w + (w, 0);
    bx.s = bx.n + (0, h);
enddef;

beginfig(1)
    pickup pencircle scaled 1pt;

    boxit.hla("HLA");
    boxit.opi("OPI");
    defaultboxsize(hla);
    defaultboxsize(opi);
    hla.c = (-hdist/2, 0);
    opi.c = (hdist/2, 0);
    drawboxed(hla, opi);

    boxit.ioc1("IOC");
    boxit.ioc2("IOC");
    boxit.ioc3("IOC");
    defaultboxsize(ioc1);
    defaultboxsize(ioc2);
    defaultboxsize(ioc3);
    ioc1.c = (-1*hdist, -1*vdist);
    ioc2.c = (0, -1*vdist);
    ioc3.c = (1*hdist, -1*vdist);
    drawboxed(ioc1, ioc2, ioc3);

    draw hla.n--(-hdist/2, -vdist/2);
    draw opi.n--(hdist/2, -vdist/2);
    draw (-1*hdist, -vdist/2)--(1*hdist, -vdist/2);
    draw (-1*hdist, -vdist/2)--ioc1.s;
    draw (0, -vdist/2)--ioc2.s;
    draw (1*hdist, -vdist/2)--ioc3.s;
    label.lft("Channel Access", (-1*hdist, -vdist/2));

    boxit.hw1("HW");
    boxit.hw2("HW");
    boxit.hw3("HW");
    defaultboxsize(hw1);
    defaultboxsize(hw2);
    defaultboxsize(hw3);
    hw1.s = ioc1.n;
    hw2.s = ioc2.n;
    hw3.s = ioc3.n;

    drawboxed(hw1);
    drawoptions(dashed evenly);
    drawboxed(hw2, hw3);
    drawoptions();

    boxit.model("Model");
    boxit.va("VA");
    defaultboxsize(model);
    defaultboxsize(va);
    model.c = ioc3.c + (1.5hdist, 0);
    va.s = model.n;
    drawboxed(model, va);

    pair deltax, deltay, o[];
    deltax := (ioc1.e - ioc1.w)/2;
    deltay := (-hdist/2, 0) - hla.n;
    o2 := ioc2.n + 3deltax/4;
    o3 := ioc3.n + 3deltax/4;
    draw o2--(xpart o2, ypart o2-h)-deltay;
    draw o3--(xpart o3, ypart o3-h)-deltay;
    draw (xpart o2, ypart o2-h)-deltay--va.n-deltay;
    draw va.n-deltay--va.n;
endfig;

end

