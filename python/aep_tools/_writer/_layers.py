"""Layer CRUD operations — add, remove, duplicate, move layers in compositions."""

from __future__ import annotations

import base64
import struct
import zlib

from aep_parser._parser.chunk import Chunk, ChunkList

from ._common import _is_chunk_list
from ._navigate import find_comp_chunklist

# ── Constants ────────────────────────────────────────────────────────────────

_LAYER_BLOCK_SIZE = 16  # Layr + Ewst + 14 view state chunks

# Default view state chunk values
_FVDV = b"\x00\x00\x00\x03"
_FIOP = b"\x00"
_FTTS = b"\x00\x00\x00\x00"
_FOAC = b"\x00"
_FIAC = b"\x00"
_FIPC = b"\x00\x00"
_FIFL = b"\x00\x00\x00\x00"

# ── Embedded binary templates (compressed, base85-encoded) ───────────────────
# Extracted from AE-generated test files. Each decodes to RIFF chunk binary.

_B85_LAYR = "c-rlnPjAyO6u_NQZ6G9=&<+T3$bka_O$?Y2x3zSCG-=b&3W!Nan;Sc=g=0syTbRTb;m&8^Gayc!;err1B*d8m!*0^8ElrxHe>S>UY7=kn%j?h2?>#?vbEEtOfZHE7;ent?K>)xz{kjZtz%;A*4)($E^;fGut6!HuXR}(L=+kl?pGnc4D)*teZZ`G5^-iIxuaK<hKjn=~eb4mud~2LSp6TB#t~^?`pAZk*JJ^H1Pgu35{6H@Ftx!d_$vqd!y%frwS=d|LyR)E2E$QByFK<Hv*5RR{w0!Nsw;$I_3(LO(sZm#>=>;%ca}ZSK8zvpEP~9`nZR>A!_S=aG$fV1KXRixh_oIo;-inxse~7h7f6OIOgtNWHNNuzE=uPZyMl2bzZ9y<o&_IhPX63k&Dx~)@1wG>zXUzKm^ek|-heB2gdRP0{!ws%p9&m+V+}I9sJ6vPK_Vbu$hq6CUv#tG0WH%$yBC^UFMA${&$57aW>EP;8?5NQZ(LC}463ORBM5Ik-aw5$*skxwp<8=atg<Vz$6w6qfn)%ZeVb3Lqu#YHa$lmsi`;)z6csM`bQ%EnOM)-t2*#UT#B0CtA<N)K5;C{IV5r1_DGgzS*#jfUV?Q^5mo-l?*0(B;%4X-OK)@eU9lVo#hw5i|*rmJ3sOL+=r%BczN;kD;|&`d}h$tgi=gwj(nQ&j<xN&NaLG#PDtsPv*@ed$a_8&|+2W-}peQjLF1A;XE{+OrgKZBT7iUn?P5tUBQyqn0Ly8>eHh5TO&Rh+WK(S!XV&@l0)wwWYImK_HEpp@86gA;tWZpj6Th;<p^fuHYnd;8eSUO;W9?pmyXDDSH|1*{xC(c6$&jIu7>Zt>}#Hqgq6owj@DDB(x2?#3>i?m8>fR6UjHLSGj>#m1T{ldbMBRU%@zAr)@Rs6|${hVWPsBUTt2*WXsyPu<H`X+)t0kF6@rMW3Ld`txG(m#5Tr2tn6c_PN9fFmJ#dn_=FLLrHn@Q9}}A&1F<cvbebQtCNn?QeWq~~03)$wxq9dBlXAVMiCvbNjdc)P6Ie1#r!!WL#m1U@XCDg8oP!8#8L=M3>>W-icirrl5&em6Foa**+%+LUz@D|m;fNg`o*c2{yP$wrYy1(hQPdrabwqgd+319;)GJWIcx58A$&W*u;M{w=frTIl$5p)Mwj1mBO1>zCY$nMpJe|i%f>SVqWnLE!PIAuhB84{LcMYCVq~^d1D%>HxLS>_Mg0JsM*NnVR>sbe^mRQFgZb(0oA9{@^7$4Gkv91lh8vNGweAoX9lt@Ku=)S&R0-rAa?5d~Dg{L$}r#0Q}FY&Y>-~"
_B85_VIEW_STATE = "c-r&v3=UynU@&nlFD^+f&&&g|Wq_E0v4C+Ih+=>Mekje5TAp75q*y@gw6c^kD4RJgGrs_$KCPsr7%G~ZmY<jm70pDj3P3C-5GyT*XtNlIHwyq$6d#K"
_B85_SOLIDS_FOLDER = "c-r&v3=UynVCC>ENzKj7Oi5*6U|`_|5}7Fl$v}#O0SYoxN)mxo2m>PnI^bm>3NT?6efqY6IkY6r0?1?w&d<qADK1V+DFL|xh#7sru4BmxPD?3*vW1Xc%7@RT>=>4Tlp7FsDI+15GC<tI%oLEBr%+rBw*MY>vp{}=u-F@b4z@tGf++%v7G@%x$B67IAjJa{W5iHF4EPTPxI+Tw^ZbGmpnn*p!2aR{vFsaA^*H4uCTA;v<5IzpVdQ~=^ioia3#h*3Un!;T$hK$2oWtzLUT=k@8HNSUK0(2$1(_)zHUH5-A`bDK%)A^>dI#m9)ZC;3P}DFoWEPYcLs%)vU^{`Vf}->!2+KFQ7^)5)cNiiWDMh&`B23k_P<P7Z=B4EqmlT!2@|GMBrxfL*nUGeJ4)!f9!9Y?GQv_;GVTf@D=Gb&d&V=VwsGLJiW^qYQMv5_zZNhMY`yE;W6o3{UjJOJsw6c^kXo<m`mI-ko$YmwPP*H}o{KRCaXeNRM&bLe;R$2~BB>>+zq?G"
_B85_LAYR_LIGHT = "c-r&v3=Uyn5P9K~SXq>lQj*BPz_0{}Wf&lU5ke&}Am|TJ+J*5y5HO$vHU@_0jq9Jbc0QfG@9D-S2Eu?5j~F8^O`#=e7C?#z*)AWjUxas*q@)*=q!cFs<yk;x0NHs!nggnbp(G_2#Mf|iadK4%DN4*MPRlRKRd6rLFD<}k7sOm{4IJk3LCs~;jW>wb*F`biF)ukIzeph<KQpfchfg4;GyEz^Nh&7B^du7?ujckl24)6+24+YcBrw=ZnLT<f<E(4{0b(jH8Wawk#Ki$lkereT@{ET=AB6AF@PL65fD&Q>`Nf$fnfZBm)DL`!F*1@DV(8)rrd$mT4VG9#l@N<JAT`9835FQNpNv#VV+>@3m<I77Qko007m4qS%EuOBhNB@yVu%@yh8S@n7Mz@zlZxLwNQg0dksM;o0~}%%c<i7lASnid@=Fp+QWc^I*Ce+{u1SVannel`|ANHi%#upNX>us$Vq()Et~BHji6z8b^U5-d6dVf*QWJ|5GV>IIQqyu$lS_z5LqvucFuYhu3^5iKx`!B2h=5zkz;H<+QoT=RdPWH_<$-FCV(e{fNC>iDAftT^F&!973XUcDx%g6a7@FzKM3_#VU!4+@v(r-)!ZM39lQ61)p_^LBDsfOk1bgu_bW0pqi9yv82PMRua!QLvTUtbgm|J2_PJUXNLU2i9QOWQLF^75w>bHzgL(C<!xFj(zIdwF|aEF+4VsS~aLU2Z6N`84UE!vVpu4E^*ZX`lIGz4SZGgDI2A!CsoXmSoYz{Hx9kzx#Fn=oA9eup-OB>==sP&N}bI{@;~uEh"
_B85_LAYR_CAMERA = "c-r&v3=Uyn;4Sh=tSrh&DM@5tU|0gg(hLy52%!=f5cCHq?E;lU11t;-&nC7!ZSH?IXV=r&`<`xWVjuvpnZtxlokL_Z8;^uR5{MI8l4b#<_|fh10sDu?t|TSBpd_U@3F0CKMj$&6NOM5-F_fg_g7_MaE>5lrAw`LK#cBCPxeD$@`K1Ne90@U(TLXu=d{A@QbmI-;^>tB9cg#!9$S+a|$j{6x!4U)y(;0r1q$Cv+V|tPakXLhiCId4AKLhiBAOOXQy_DIb*D}t!_8%ao;-W#}z)4&@-~`Dji6GB-IP^jI4h;_&C;=!T7LZ?@S(2Hbhe!RuhZrLxc_D@_eqhPf(9mFsHB<?)cmq;HjG17FLHx-`l{CgcMu=$;A0nl>AbXMczNma`A!axlVkCx`(P)Sf7h=K5i8-nG&4Yv(qZi2`#yr3wR)NP3ngWtyASk~iu_RR?if~PGi{zSQ2&Gx15b-ZaOwKH+B%CIPVlE~&4dO~e4v|<w%r&npvq-_QpddA|NFg&%At*I1CpEc*h%`iGhylZkg~SkJVWE47A%zIIl?)7*6e86-C+4OWB?6NksQM_z+Q^26U>F(gYf@c9gnFoJV%#%RQqv*5A`Ub;hn&pflAMebV<6jv;R5$Nw3f60v=_sOqc_6<0IF8A8~"
_B85_LAYR_ADJUSTMENT = "c-rln&1(}u6u@U=Xca+3JXG<p2M?l@`ccGN6Vne0EtN)#g+iU|%qD}gGt0~*TJRt7?%&|wAf7zyMZ}vRo;_G+vYVQu+0AD2(VFf+_9L0RefiCs_ujn8#(McF0CzrYzym>%f&hSb`gI-TfN56q2ws4H=U?GDH>(fVKxeaB-{{kF9p6dOo+<Z{Id3%ezx__3s;`i&=(qAlroLwSe7@CBA<x|3DlR`>v7ZtT+uPWKzE4=Sr~E)J_^nVyw#hvg%DoiIotfXiyT356doAj_H(%a{1gyhDLuu*y!*4%sl;)Ry1yZBVM$-#mxaJ_J%r8vZU!l5Zp4)c6*?HeiOh6`GE<Afp@VXyOZ1#4<NE{>9CjAMQL=n#R??!5yjYn@{_cCJ1h;0dinSusdJTWWBl~f_Uk16OGzc^!#1JJX;Tn~k;6!hl$*uzb(ULJ6TU|io0a@$;E!}jx-XNR&sPqVEZC$gInX%Sgr4I=EK?_(%z!gO$TDR$K8h-e=90g2@EBO=l!GdYoFoYY)U!u~n|!@@4B1Bzv=P0jr2im>MrMA*j^Gh}c1#{J3OF+3cf?<u4gQ6qdppX>naq{t2iB{@KUB)DI$LBwAzU<NA`quANpt$l8^+7rgGNTAMSwBdDy#TxC0W|C}9jW!kBz;wl{a4Ap0NI5mZJ-qt751I*SBRM5#l~8&rMye_xGKpV5g(jno50#!&tS_C(XyXc)#B3&{O{)G+C}cQMT-!+z*9O&Q<+T!$#i|poF=}aIxN$o6G7&nlide-AnRVuZ8qd_`SerU)7X;Fn5ef)iEu<Kq5|m2XLHw5ESQVUP4xDOLutBOd71WMAB4sb5J-bzk!fp>@MaRK@ycM0XbySN;)0QO2h=jIbmpJ7jzLIriU?TZu^(r^;tg@`pRIgqX_*XE_)@fVKdWCE&SeU4Are~X1G1;;<F6_F*G1t@Mu?xFn@Yu`5b?XvODY5l25G(uGsZ%IokY&WWJU(HBVJV}L{l~<vj)B-FRyxg(nUk3x>)z8i3V@N=vRu7$^+~y2)5K28%*Hy1tqLp|rqdZK$6{m6wX+WeX3jwbwv1R0V)iztl)G;B&xroS))~UDZSI;7AYjkh;&8+c4^NI*@>NhktkwUB*eL3b#X2H9dT(^XRqAD^V7xLB+T_QfO|b91)xbg!gySk+m$w>g_e;Jgg={9tEZm*PN`g}`f@NM84o<Squ$Mxc@V5rfC{nXw1r_d)UZJwl+QHY?q-#Xpr}eA@R!gjZ9&SiKkso@FC+Hv2*;~_wUJd?hd%o+l0wq$>8hW6w7s02CKfCH_m&09}qurYB_7@3RAou"
_B85_LAYR_NULL = "c-rln&5ILB6u_%v7!_faMNq^;A3Q9|;Kz#W&BV+H12c?FR2&e-N>_DKY;{#rRf!IGko_+fPlA^{EnXIO5Bmq~X^*0pWpPjt7SDTdtV;KcNl&`d>3qzX>4K!XNp;ohU%h(o)vGKoRqp_B>D4ma6ci~40C=H4XF&m&Vzs})L-3{k7}VC&qx#|u=q{Fd;@vNQZ2kKC`<KtRp8dJ?@+Z)v6uO?tQ0^-C2VI?vj<wu=pNlUPs{0Dbnr>4xW9Vz9>to?_Kq1fEe^;KnHE-V`9=6x82YsKgde8BKe!>3=)nrG%N5X!;3HzOy-MF%Gc~-Z&uJ4|_`8gm0tnF<>?dG`~|9&`MnZ5Zj=ryi3k{$=c6$e3O-Y{)@g_@ojx8r`L`@WNyfK0kvc=n>;O+TL4(Tg!Nv4>bk@3*-mig31ZC05#eK6(?oniES$Y*i4<6g1G1iCG1%qzdW%m4TkIlQZUf0D6|Tz<Z08f!^6Z`f!1(A2+!|FsW@9xizk_Vf%i<*kRwVr&-tb5?RlQ>=2n}Eh6l)?_(%z!nAXBDR$K8h-e<g0f`igBO=n#XL=%SKdHH(l<jpuhJ{^Kn-t4LotpU+@vuiyc-UJMGi0y&#{9|NK0KVCw;6gbqgFUVpXdPG%Mcw5N^*eqNN~T}fQUc3j2Wy^j1pIKRQkebr6-JGkwTowNW+^7i$&TG%_P|z7-?#_h3ULk<5C`gnQ|I}dwAh~A2bt^MsiBf0-^Lk%v4=KWCFi_0!>C5A1b}5SYJAmk;WA;joM5|noR9)Q^;^CzjiN!UmH}K`Nv8~mMBiR$7p2n;l}9Lb42LCDrOfmWYk#*az0ZVW3A|@T@XkUW+)(dx|CslDo`qE2mV`*V^^@BF>t0`!7`~gRFFIJh?KpQ_V8vYO6xs{l^qBB$y#*C_E9@T+PWk`P9)R~yTU0K$(gKg2PRT%XRitauPVzLP4?<xiT?w}S-N$rov)A`2@B&D4)tpDY9?CN%7tB*IOckKEOu#q3>JHixNcM8DJ8Zv24YnoJ535j0<xS~#Nrc17?v^~*;h>L^caY(V5P(Sgf*GlvFMq`t^<t4mdEPdyHCpXo+fcw<~r6zY(ZejFr7|cITjsj@11=pFmpCzu;s*h5VO}frQCJ%e@65tw!{#AY;)JR00DdE7KbCYy}f_L((i%-Vms}3iH#!fSZ*T1<IhGXoTZ+F3MLB^BTaD}(gf$;t1T=9K{zSnb!xS>c&*}#O2}rC%)--otRy%9Gg#$K;ovmq3=c9$6TWLOMwyxeE2wZ+?=>o0J16-1nnY&gx2%?Rz-)>2#lj6~CyGO_@f7VtIu91LqSu4}-X4qmR-!~I+Cbmy>+9g}6aPi>X{W+dn%&cyX!#5tW;fs"
_B85_LAYR_SHAPE = "c-rk+&5I*N6tB+2%!rE&vdADF3h}UrVRvv@ylt{GnPFgt9cI>LM}*l*S9MZY>1wJfvzx_(coF;$#EXb$!HWk$*|T`?te_$e9t7F52em5QiAkqFlFlTP&E!E+T}kz;*T47b)qAgccjxd90L7noQA;qa5CGtF{dp1OfFY~>4eo>g+b4c&fe*nTSzrZ#({Dce<D;)mKl%3b%MU;_<@)X!q&!HWx0LgyZZ7rCwcCD{*S}D><|!<z0Ut|WySiNo?g0unO#e!G^Hv2OaIWB8Vk<5r+!nm)4b0{9Exg^&H{ap=e89I*Jic~(wb;kqXB@+~m-{o{$4I>za9?iofa@TFzf79I=bwk!r9Z4AkH8{4(A{Y6*4Hu8uLay!&ArI2F#`9Is>AiDdCVAiNFR~dr?6g8xGE#&8F-57b=`aKr;oLzY5V$Dld;;HFWva<&zCofH=p=i<62`a&w}yD#>k+xUuyaNPCG6s+-w;69{*D6^!H4^)a~~m>l;nQ#Yz04>=k)+YHOWuQN|)Q@o9|4yP7a}M(er#&jx2)#OnElk@cJh%f_#atY^!L@?xXw`F@H2>g##ueNfO2vSdSW>9KBu-^bVc7<$cU2X_Q=rNc!d!om2O0(aBwAi}R?lx7bpA}C_=e5IN6_$1K#o_6`Q3{ShyB~_HW$Jb(|39$S-v<8<_*Pzv2Io7%P+AE{_(4PKYe?JPb^#x+XA$D6(;wof7OGeDfaV1rN-gg<$Gd{myzDGdM0&C!GeEwRBJ-o`*yDhFTN*WuAMm1~%-b<J};Qiw~+u9%^M+-zch*aDYDqz|32ojLGI&5}WC^8=p5sgQFL`3rWGeV??=j5Uxo$L~w)~FUEGSQ|A|Acnfr6G3MTa36E-u8_9i^<Fa{rsMRdl{buGo(ZZvla_s!9ATxV*cPNaZ!~KoVc39(&x@rdg{7F3?a^Rq~T2+*>1BmXr_tH%t%uuCxlfRRW9WWXv(e&-XL4|QlOcVG?FulO*%ajnyLweP2iU%&~&8nkkX6FO+{xq(l`PQV>VNgCe!%JLnWk}xUmIMeLc&rX_h(Mq(X->F?qw7abC`^V9#w-(<zT6XvjzKaw&s;Hjq>j`a7naL>zveQD>$&e3#bh%CFWmsFYDgdvWUmrK1SM%C=3sWGlL0nM((ewk=7pKqRn@xZ{DOGlHe3=Zs)d)Nfnu3W4k?5tv=!La(+))x@XTxQOFW+g#6&$1WXBz+-Px$7xD3r-<!L0I@@l*iD8+0%QxsLLQ&G)Fo2JL-rISc6kDb?Gc4o(wbcOvG6HEcLR)tZ4s;YXP=DgoF;KuE^Mq1u`NNQOW1twl@qbCcJAyUL0r2P1KR?z2*lt4XN)_};$4Jv#CBXv9zyPzEkK~i+TwVKo#VTOBV<87Vx93_#LlAbSZ-p<6JK$St7<PzpsF35?Gh!y3`jG?_&}O>wkakx{|)Sw(0?UHrDApbhQ7WIet7P$P#t15sBU+w++q3;<ok{v"
_B85_LAYR_TEXT = "c-rk;O^h5z6|VhBvW|Z+kt3X7J7o!w7qK(d|I;MIUaxmI7Q2bHYmBYkk<+`~v)f9~^r*YX@d~(rkh#DKfucYp2q@x^0}|rM0d5=+2TpK7z=i`T$^{Mt+|*y!bkFwudUvy4Puo+~)m8QCz3;txud2H3g{#Zg0eI<K3)WWP*^vbR_zC_!4MqXEMraCN1<m|}q<jzTyhccm_r7;;``zzvzxk`}pMM?XU!$2mJFhX&<@!=oDdFr`daMO1%lysA-l#`*xQ6S;34MHD!}$d710uUh$`_`uT%Lv3ox2gd7Wj21h+HSk8;j9BKi-D!2~PL%soUswacU>^EB<<;>eQlqNf`C#&aGi`>>m6wve&|1Mp{#G>8pQwgW-;U<3u+XpVj~Jk25n<7e8Plw99e(3Gjf|x@|?AOD@T|Wh}{SuxOUx3opPTf|3GXe39IcqQoDr@SLQk35zqn?_J-jJ9B<5N}eNl;eHGjfeV&_1!^D!Q@G>+8$W4)>Lj5i!J-UhSk!3S8@M*W?OfpF_7JF`01*D8OcEB@-`>aF!n9mGvW>@G!W657i%Bvd>Yv<oOsb063&G1ceZ5H#T*Klmg6ov9)J_ruOCkYj06C^H|2|m5^sZt`cQC~e%u%XQt1M-zC^bh#jMPh*-vHQ?gvsX9^I&xnd=B&XdGI{A2+H7V;K%S3d<LF{==|9EBWMJTqQ}q?bQB#&A44BUPorrxgJ#h@x{B7(H_$iHJ@g&)Ci(&TA$kk_2)&Jdirzs#L%%_PMce4_=za7r^l$Vb`Y-w)x*w0kkHtsgWATaj+4z(3bMY7AGPMN4%IXEM0=@#?2JgVr@C=$jPoiV!1UiYHLZ{-fcs!nnVf=i&5^qz{aTm<!r{QOCNg*Y|Dj_{dP>}MlW+E?R{3;Z`6c9w>99fA>A9Bvy@ZG}fDa<BjvIiFBwC*siL}jSSwA56r)>g4EV|fB<jvltPB`^;zWBNL8A=8N_7Z72nVtJuMc;PoHjDm(kh|30Pp+kve2FpsAm7)m|xt9>n>8zEA<rT4SAgM}Ijix$H4c@lI$xCK3pp3+wB<=)XvS3VB#hoVZba7{hyOOvQV<-f|q9W)kO}PbqMbK9?0+FIKmKB4RsN{-CQdMxQN~BJuqN@srx1h0Ur_wq~OVy!)Q-ijnlvEQ=QA9PA+(_iPCOFd+;S84DYTa|LS#H`FNX$S;UzGZlx&0J1^#S{9E&VThPR(`#R;eduB5>Cd)oKEET>zz1;dBa=t}t8DRjATjV?gUVW(S+SZt$D}rBlcasz5`6Do$nA-cWch6lVy-Foa<k24~Ai_%qC&fk}QDU`j%&5|yeXLxs)_h3A5w5}g4hy=A<aMi}|kIme0`fx}4R>4m5;rG!h9OKEZ`O_k@#tY`CyxrU<2_0hq7FrT6K=`+M=bS&mF*tB37=PFSl0gt!}S-1*5-4WEOr;w?qkW-#Q(F@F3@RmB6K*V9Jz(R>@0MF7gbsj4%wo3d+R#j!{QS=sXf?7NYqFw}1zfr8YUdEM_l1FL(fngx{VIRU6#x5jzL?yxQ!=SE1qOOBcQ0R<TghvwoL#Dn1b=OxZM_+X0BAG4Jb4+ouCAJn*@dJt#b1PW*0+O}nNC{~|J?X({8{~n>)(|W>fh&07GCi4E?<J{{=9jdDB51QkO|#~>sL@+$j))qRt%0kPqDpJ&G}f*LfwnBXD{9!vvCO4MLfC?ar!PhVo0>w*nU!^3HekUZy5LhYr6?Zo&xqiDHVN$TG!5x=Au*Yb-@MB?(dC@z@=R_QnRh`?CSB0cRJGE%THQI|nN+pbxmxdBZS)U7seb^>{<}!>0IE?27)Kpo9BqI;`T)G;Kz%lCS8`|N%1W31T4&3X^T+RO>xr(>SwZt$+SrpRhmMK*<CBR86+WD-H~AVlGgo_YbeJf@mxNeKa)}k_14%;7Qo4>wMjueoTAf6f-E4VB7!dx;xwrD=8~0aNFH>Kdzw8%{Q!V6&J7`NZXtNPyl@@ozY+gHP$VLN&?4mA0HwIYiwz|ry1~r>e%P6648?geC_Fx~D%#`6qZ1*-|S)1;EBUX?l32$Ap*>Fd8D0XBSPtot<o3f2sHwd`#ijd^mjPNeahjYw5(BqtJ&C-tIjwTD#gG?DxK{8EKqn<=o3Yuw_H0n^&RYtmsyZmN7DT(@Wc9>;KSgb~6k|cqJIxQo;R83kam;w>EOd4yX(F${=l1>LxNvg;+Rh0sEMrG<26Sqg=Gq#p;YVZ|CPNJ0g7QukY)`|E>)U-*m`O-6oCK;jT^H5;yq;X(d(NdFIvoV(=)!58!W|j)NQo_cWZYrTnBodyOPF<;KKp9!3B$~?^%_=F)VvnDy!d^e6^dw+0oaE-40ZGxY2a=G9J*!#54jiwc@Dx-M28cjiRYy!+j7*g-F|EjA96ce}r7!KKi0N7Go+Ptvcz!xOKOLT*9`0yeRE9^Mdw%4}-z@`mE!t?*HySR!Kl#QVqQ=TUzxa!9|E{v}-Cw`=iR5|fJL;VG{Z_OIU#Ul~Ukls4kq0*hc;7!C_>DT8t=aA0nD69f(Z^<a5V+}^`@pJ&6+fu5p6$PGc;d4IaDUAYU4qGN)Rr5L&3{_Hml*5ydx<#i>w5_RCXVdR_YxO+Z6Dc<Dj7FbUd)#B5R-<8^@i9hf$P*Fi-6V{v5`?f3L}o*ZwEl{3G$qzeSM#EI`<o^{?R+##U4K8N3U)9k!^Kqn?Y{L$FMo@W{0sk?LQu7Tic1qtsx=_BD1wSZUCq2b;k;zTZ2nZ#dFr9-9rT9G2SO4<Kw%8NQ!3fi1Zs_7pyJ316Yo>y!=lS1%i*?Z;7yDJw#Z#!$?*h`7xa9=Whd0pSJJt5xT4n4%*tr4*dG^re*uD7oD25<~er9+1$$g=<agw)@n}B13UY}jo*lzVBYHn&3<BYV7OUx?l|6Tb<GdM1E8t(&A_iZb2qy{vrpWFzUSI=uIC*HO>G30O%{IL7}_6h>Q;m&Rjn&J`@>BouzE3@ed1=I_Oo}RAgpx^Y<yL}IY`tb(;QxL1H6=Jvu}97b>1lZw-$$XRkMiK$$@Km9W=xcJauUR{mfWl6ham;!@XFCf0V1vf!5&*?#5=sPHU=e80H!6qkArJ=~fP6)9dR_y|WcPVmp@v5o${z7$U-L1J3xKA9OxDda7?k#_4&{Xy3DHWMp^Fi(b9t{~7G%m9;H;LJ+2o2zDHWKWekBx<=Ng*tncZ#a(xE{`KI)>#;B0+5?Y$#jR8tp>s$PySfL6E!Um(hGzvGAR8jq;_=;@TXVv&J!B6tVyE^1u|+4s%lr;=a_Gle-y(<r*cP_oT0Oh_^nARh={PNiHkLtbE^xw{;~maexhFP8_s(@IaBAyYZD1QBmV+2v@;%S5REFOobVuxJ&35iWzd}MlVC9}IJ{V$g{LvxS`!0wfmb4d$?Z&y|bi;Q2_HQFQoNABl!KpTXx9db9H~`%A(4KR%I`7)f2K&E)CR*w)d2Seao3?`QRq*?x@3)*ooaCq5;*`7f`aht@0s#"

# Cached parsed templates (loaded on first use)
_template_cache: dict | None = None


def _decode_b85(b85: str) -> bytes:
    """Decode a base85+zlib compressed binary blob."""
    return zlib.decompress(base64.b85decode(b85))


def _parse_chunk_from_bin(data: bytes) -> Chunk:
    """Parse a single RIFF chunk from raw binary (big-endian)."""
    from aep_parser._parser.riff import AepChunkParser
    # Wrap in a minimal RIFX envelope so the parser works
    size = len(data) + 4  # +4 for "Egg!"
    header = b"RIFX" + struct.pack(">I", size) + b"Egg!" + data
    parser = AepChunkParser(header, 0, True)
    root = parser.parse()
    return root.data.children[0]


def _parse_chunks_from_bin(data: bytes) -> list[Chunk]:
    """Parse multiple consecutive RIFF chunks from raw binary."""
    from aep_parser._parser.riff import AepChunkParser
    size = len(data) + 4
    header = b"RIFX" + struct.pack(">I", size) + b"Egg!" + data
    parser = AepChunkParser(header, 0, True)
    root = parser.parse()
    return list(root.data.children)


def _load_templates() -> dict:
    """Decode embedded binary templates into chunk objects."""
    global _template_cache
    if _template_cache is not None:
        return _template_cache

    layr = _parse_chunk_from_bin(_decode_b85(_B85_LAYR))
    view_state = _parse_chunks_from_bin(_decode_b85(_B85_VIEW_STATE))
    solids_folder = _parse_chunk_from_bin(_decode_b85(_B85_SOLIDS_FOLDER))

    # Extract footage item + view state from solids folder
    sfdr = solids_folder.data.find("Sfdr")
    footage_item = None
    footage_view = []
    for i, c in enumerate(sfdr.data.children):
        if c.name == "Item":
            footage_item = c
            footage_view = [ch for ch in sfdr.data.children[i + 1:]
                           if ch.header != "LIST"]
            break

    _template_cache = {
        "layr": layr,
        "view_state": view_state,
        "solids_folder": solids_folder,
        "footage_item": footage_item,
        "footage_view": footage_view,
        "layr_light": _parse_chunk_from_bin(_decode_b85(_B85_LAYR_LIGHT)),
        "layr_camera": _parse_chunk_from_bin(_decode_b85(_B85_LAYR_CAMERA)),
        "layr_adjustment": _parse_chunk_from_bin(_decode_b85(_B85_LAYR_ADJUSTMENT)),
        "layr_null": _parse_chunk_from_bin(_decode_b85(_B85_LAYR_NULL)),
        "layr_shape": _parse_chunk_from_bin(_decode_b85(_B85_LAYR_SHAPE)),
        "layr_text": _parse_chunk_from_bin(_decode_b85(_B85_LAYR_TEXT)),
        "layr_precomp": layr,  # precomp uses same tdgp as solid
    }
    return _template_cache


# ── Deep Copy ────────────────────────────────────────────────────────────────

def _deep_copy_chunk(chunk: Chunk) -> Chunk:
    """Recursively deep-copy a chunk tree."""
    if _is_chunk_list(chunk.data):
        new_children = [_deep_copy_chunk(c) for c in chunk.data.children]
        new_cl = ChunkList(chunk.data.type, new_children)
        return Chunk(chunk.header, chunk.length, new_cl)
    elif isinstance(chunk.data, (bytes, bytearray)):
        return Chunk(chunk.header, chunk.length, bytes(chunk.data))
    elif isinstance(chunk.data, str):
        return Chunk(chunk.header, chunk.length, chunk.data)
    else:
        import copy
        return copy.deepcopy(chunk)


# ── ID / Navigation Helpers ──────────────────────────────────────────────────

def _scan_max_id(chunk: Chunk) -> int:
    """Scan all idta and ldta chunks to find the maximum ID."""
    max_id = 0
    if isinstance(chunk.data, (bytes, bytearray)):
        if chunk.header == "idta" and len(chunk.data) >= 20:
            max_id = struct.unpack(">I", chunk.data[16:20])[0]
        elif chunk.header == "ldta" and len(chunk.data) >= 4:
            max_id = struct.unpack(">I", chunk.data[0:4])[0]
    elif _is_chunk_list(chunk.data):
        for child in chunk.data.children:
            max_id = max(max_id, _scan_max_id(child))
    return max_id


def _find_dlay_index(comp_cl: ChunkList) -> int:
    """Find the index of the first DLay chunk."""
    for i, c in enumerate(comp_cl.children):
        if c.name == "DLay":
            return i
    raise ValueError("No DLay found in composition")


def _find_layer_block_start(comp_cl: ChunkList, layer_id: int) -> int | None:
    """Find the start index of a layer's 16-chunk block."""
    for i, c in enumerate(comp_cl.children):
        if c.name == "Layr":
            ldta = c.data.find_optional("ldta")
            if ldta and isinstance(ldta.data, (bytes, bytearray)) and len(ldta.data) >= 4:
                if struct.unpack(">I", ldta.data[0:4])[0] == layer_id:
                    return i
    return None


def _count_user_layers(comp_cl: ChunkList) -> int:
    """Count user Layr chunks before DLay."""
    count = 0
    for c in comp_cl.children:
        if c.name == "DLay":
            break
        if c.name == "Layr":
            count += 1
    return count


def _layer_insert_point(comp_cl: ChunkList, index: int | None) -> int:
    """Calculate the children list index to insert a new layer block."""
    dlay_idx = _find_dlay_index(comp_cl)

    # Find where user layers start
    first_layr_idx = dlay_idx
    for i, c in enumerate(comp_cl.children):
        if c.name == "Layr":
            first_layr_idx = i
            break

    if index is None or index <= 1:
        return first_layr_idx  # top

    num_layers = _count_user_layers(comp_cl)
    target = min(index, num_layers + 1)
    return first_layr_idx + (target - 1) * _LAYER_BLOCK_SIZE


# ── Chunk Modification Helpers ───────────────────────────────────────────────

def _build_view_state_block_simple() -> list[Chunk]:
    """Build 7 simple view state chunks (used at Fold level after comp Items)."""
    return [
        Chunk("fvdv", 4, _FVDV),
        Chunk("fiop", 1, _FIOP),
        Chunk("ftts", 4, _FTTS),
        Chunk("foac", 1, _FOAC),
        Chunk("fiac", 1, _FIAC),
        Chunk("fipc", 2, _FIPC),
        Chunk("fifl", 4, _FIFL),
    ]


def _set_chunk_id(chunk: Chunk, field: str, new_id: int) -> None:
    """Set an ID in a binary chunk's data."""
    if not isinstance(chunk.data, (bytes, bytearray)):
        return
    data = bytearray(chunk.data)
    if field == "idta_id" and len(data) >= 20:
        struct.pack_into(">I", data, 16, new_id)
    elif field == "iide" and len(data) >= 4:
        struct.pack_into("<I", data, 0, new_id)  # iide is always little-endian
    elif field == "ldta_layer_id" and len(data) >= 4:
        struct.pack_into(">I", data, 0, new_id)
    elif field == "ldta_asset_id" and len(data) >= 44:
        struct.pack_into(">I", data, 40, new_id)
    elif field == "ewin_layer_id" and len(data) >= 24:
        struct.pack_into(">I", data, 20, new_id)
    chunk.data = bytes(data)


def _set_ldta_times(ldta_chunk: Chunk, duration_num: int, duration_den: int) -> None:
    """Set layer time fields to match composition duration."""
    data = bytearray(ldta_chunk.data)
    # start_time = 0
    struct.pack_into(">i", data, 12, 0)
    struct.pack_into(">I", data, 16, duration_den)
    # in_time = 0
    struct.pack_into(">i", data, 20, 0)
    struct.pack_into(">I", data, 24, duration_den)
    # out_time = duration
    struct.pack_into(">i", data, 28, duration_num)
    struct.pack_into(">I", data, 32, duration_den)
    ldta_chunk.data = bytes(data)


def _set_opti_color_name(opti_chunk: Chunk, name: str,
                         r: float, g: float, b: float) -> None:
    """Set solid color and name in opti chunk."""
    data = bytearray(opti_chunk.data)
    struct.pack_into(">f", data, 14, r)
    struct.pack_into(">f", data, 18, g)
    struct.pack_into(">f", data, 22, b)
    # Name at offset 26 (NUL-terminated, 256 bytes max)
    name_bytes = name.encode("utf-8")[:255]
    data[26:282] = b"\x00" * 256
    data[26:26 + len(name_bytes)] = name_bytes
    opti_chunk.data = bytes(data)


def _set_sspc_dimensions(sspc_chunk: Chunk, width: int, height: int) -> None:
    """Set dimensions in sspc chunk."""
    data = bytearray(sspc_chunk.data)
    struct.pack_into(">H", data, 32, width)
    struct.pack_into(">H", data, 36, height)
    sspc_chunk.data = bytes(data)


def _read_comp_duration(comp_cl: ChunkList) -> tuple[int, int]:
    """Read duration rational (num, den) from cdta chunk."""
    cdta = comp_cl.find_optional("cdta")
    if cdta and isinstance(cdta.data, (bytes, bytearray)) and len(cdta.data) >= 52:
        dur_num = struct.unpack(">i", cdta.data[44:48])[0]
        dur_den = struct.unpack(">I", cdta.data[48:52])[0]
        return dur_num, dur_den
    return 61440, 24576  # default 2.5s


# ── Solids Folder ────────────────────────────────────────────────────────────

def _ensure_solids_folder(root: Chunk, next_id: int) -> tuple[ChunkList, int]:
    """Find or create the Solids folder. Returns (Sfdr ChunkList, next_id)."""
    fold = root.list.find("Fold")

    for child in fold.list.children:
        if child.name == "Item":
            utf8 = child.list.find_optional("Utf8")
            if utf8 and isinstance(utf8.data, str) and utf8.data == "Solids":
                sfdr = child.list.find_optional("Sfdr")
                if sfdr:
                    return sfdr.list, next_id

    # Create from template
    templates = _load_templates()
    solids = _deep_copy_chunk(templates["solids_folder"])

    # Update folder ID
    folder_id = next_id
    next_id += 1
    _set_chunk_id(solids.data.find("iide"), "iide", folder_id)
    _set_chunk_id(solids.data.find("idta"), "idta_id", folder_id)

    # Clear the Sfdr (remove template footage item + view state)
    sfdr = solids.data.find("Sfdr")
    sfdr.data.children.clear()

    fold.list.children.append(solids)
    return sfdr.list, next_id


# ── Public API ───────────────────────────────────────────────────────────────

def add_solid_layer(root: Chunk, comp_id: int, name: str,
                    width: int, height: int,
                    r: float, g: float, b: float,
                    big_endian: bool,
                    index: int | None = None) -> int:
    """Add a solid layer to a composition. Returns the new layer_id."""
    comp_cl = find_comp_chunklist(root, comp_id, big_endian)
    if comp_cl is None:
        raise ValueError(f"Composition with id={comp_id} not found")

    templates = _load_templates()
    duration_num, duration_den = _read_comp_duration(comp_cl)
    next_id = _scan_max_id(root) + 1

    # ── Create solid asset ──
    sfdr_cl, next_id = _ensure_solids_folder(root, next_id)
    asset_id = next_id
    next_id += 1

    # Deep copy footage item from template
    footage = _deep_copy_chunk(templates["footage_item"])
    _set_chunk_id(footage.data.find("iide"), "iide", asset_id)
    _set_chunk_id(footage.data.find("idta"), "idta_id", asset_id)

    # Update sspc dimensions and opti color/name
    pin = footage.data.find("Pin ")
    _set_sspc_dimensions(pin.data.find("sspc"), width, height)
    _set_opti_color_name(pin.data.find("opti"), name, r, g, b)

    # Add footage + view state to Sfdr
    sfdr_cl.children.append(footage)
    for vc in templates["footage_view"]:
        sfdr_cl.children.append(_deep_copy_chunk(vc))

    # ── Create layer ──
    layer_id = next_id

    # Deep copy Layr from template
    layr = _deep_copy_chunk(templates["layr"])
    ldta = layr.data.find("ldta")
    _set_chunk_id(ldta, "ldta_layer_id", layer_id)
    _set_chunk_id(ldta, "ldta_asset_id", asset_id)
    _set_ldta_times(ldta, duration_num, duration_den)

    # Set layer name
    utf8 = layr.data.find("Utf8")
    utf8.data = name
    utf8.length = len(name.encode("utf-8"))

    # Build view state from template
    view_state = [_deep_copy_chunk(c) for c in templates["view_state"]]
    # Update ewin layer_id
    ewst = view_state[0]  # First chunk is Ewst
    ewin = ewst.data.find("ewin")
    _set_chunk_id(ewin, "ewin_layer_id", layer_id)

    # Assemble 16-chunk block
    block = [layr] + view_state

    # Insert into comp
    insert_at = _layer_insert_point(comp_cl, index)
    for i, chunk in enumerate(block):
        comp_cl.children.insert(insert_at + i, chunk)

    return layer_id


def _add_layer_from_template(root: Chunk, comp_id: int, template_key: str,
                             name: str, big_endian: bool,
                             asset_id: int = 0, ldta_flags: dict | None = None,
                             index: int | None = None) -> int:
    """Generic helper: add a layer from a named template. Returns layer_id."""
    comp_cl = find_comp_chunklist(root, comp_id, big_endian)
    if comp_cl is None:
        raise ValueError(f"Composition with id={comp_id} not found")

    templates = _load_templates()
    duration_num, duration_den = _read_comp_duration(comp_cl)
    layer_id = _scan_max_id(root) + 1

    layr = _deep_copy_chunk(templates[template_key])
    ldta = layr.data.find("ldta")
    _set_chunk_id(ldta, "ldta_layer_id", layer_id)

    # Set asset_id
    data = bytearray(ldta.data)
    struct.pack_into(">I", data, 40, asset_id)
    ldta.data = bytes(data)

    _set_ldta_times(ldta, duration_num, duration_den)

    # Apply custom flags
    if ldta_flags:
        data = bytearray(ldta.data)
        for offset, value in ldta_flags.items():
            data[offset] = value
        ldta.data = bytes(data)

    # Set name
    utf8 = layr.data.find("Utf8")
    utf8.data = name
    utf8.length = len(name.encode("utf-8"))

    # Build view state
    view_state = [_deep_copy_chunk(c) for c in templates["view_state"]]
    ewst = view_state[0]
    ewin = ewst.data.find("ewin")
    _set_chunk_id(ewin, "ewin_layer_id", layer_id)

    block = [layr] + view_state
    insert_at = _layer_insert_point(comp_cl, index)
    for i, chunk in enumerate(block):
        comp_cl.children.insert(insert_at + i, chunk)

    return layer_id


def _create_solid_asset(root: Chunk, name: str, width: int, height: int,
                        r: float, g: float, b: float,
                        big_endian: bool) -> tuple[int, int]:
    """Create a solid footage asset. Returns (asset_id, updated next_id)."""
    templates = _load_templates()
    next_id = _scan_max_id(root) + 1
    sfdr_cl, next_id = _ensure_solids_folder(root, next_id)
    asset_id = next_id
    next_id += 1

    footage = _deep_copy_chunk(templates["footage_item"])
    _set_chunk_id(footage.data.find("iide"), "iide", asset_id)
    _set_chunk_id(footage.data.find("idta"), "idta_id", asset_id)
    pin = footage.data.find("Pin ")
    _set_sspc_dimensions(pin.data.find("sspc"), width, height)
    _set_opti_color_name(pin.data.find("opti"), name, r, g, b)
    sfdr_cl.children.append(footage)
    for vc in templates["footage_view"]:
        sfdr_cl.children.append(_deep_copy_chunk(vc))
    return asset_id, next_id


def add_null_layer(root: Chunk, comp_id: int, name: str = "Null 1",
                   big_endian: bool = True,
                   index: int | None = None) -> int:
    """Add a null object layer. Returns layer_id."""
    asset_id, _ = _create_solid_asset(root, name, 100, 100, 0.0, 0.0, 0.0, big_endian)
    return _add_layer_from_template(
        root, comp_id, "layr_null", name, big_endian,
        asset_id=asset_id, index=index)


def add_adjustment_layer(root: Chunk, comp_id: int, name: str = "Adjustment Layer",
                         width: int | None = None, height: int | None = None,
                         big_endian: bool = True,
                         index: int | None = None) -> int:
    """Add an adjustment layer. Returns layer_id."""
    comp_cl = find_comp_chunklist(root, comp_id, big_endian)
    if comp_cl is None:
        raise ValueError(f"Composition with id={comp_id} not found")
    cdta = comp_cl.find_optional("cdta")
    if cdta and isinstance(cdta.data, (bytes, bytearray)):
        cw = struct.unpack(">H", cdta.data[140:142])[0]
        ch = struct.unpack(">H", cdta.data[142:144])[0]
    else:
        cw, ch = 1920, 1080
    w = width if width is not None else cw
    h = height if height is not None else ch

    asset_id, _ = _create_solid_asset(root, name, w, h, 0.0, 0.0, 0.0, big_endian)
    return _add_layer_from_template(
        root, comp_id, "layr_adjustment", name, big_endian,
        asset_id=asset_id, index=index)


def add_shape_layer(root: Chunk, comp_id: int, name: str = "Shape Layer",
                    big_endian: bool = True,
                    index: int | None = None) -> int:
    """Add an empty shape layer. Returns layer_id."""
    return _add_layer_from_template(
        root, comp_id, "layr_shape", name, big_endian,
        asset_id=0, index=index)


def add_text_layer(root: Chunk, comp_id: int, name: str = "Text Layer",
                   big_endian: bool = True,
                   index: int | None = None) -> int:
    """Add a text layer. Returns layer_id."""
    return _add_layer_from_template(
        root, comp_id, "layr_text", name, big_endian,
        asset_id=0, index=index)


def add_camera_layer(root: Chunk, comp_id: int, name: str = "Camera",
                     big_endian: bool = True,
                     index: int | None = None) -> int:
    """Add a camera layer. Returns layer_id."""
    return _add_layer_from_template(
        root, comp_id, "layr_camera", name, big_endian,
        asset_id=0, index=index)


def add_light_layer(root: Chunk, comp_id: int, name: str = "Light",
                    big_endian: bool = True,
                    index: int | None = None) -> int:
    """Add a light layer. Returns layer_id."""
    return _add_layer_from_template(
        root, comp_id, "layr_light", name, big_endian,
        asset_id=0xFFFFFFFF, index=index)


def add_precomp_layer(root: Chunk, comp_id: int, source_comp_id: int,
                      name: str = "", big_endian: bool = True,
                      index: int | None = None) -> int:
    """Add a precomp layer referencing an existing composition. Returns layer_id."""
    return _add_layer_from_template(
        root, comp_id, "layr_precomp", name, big_endian,
        asset_id=source_comp_id, index=index)


def precompose_layers(root: Chunk, comp_id: int, layer_ids: list[int],
                      new_comp_name: str, big_endian: bool) -> tuple[int, int]:
    """Move layers into a new composition and replace with a precomp layer.

    Returns (new_comp_id, precomp_layer_id).
    """
    comp_cl = find_comp_chunklist(root, comp_id, big_endian)
    if comp_cl is None:
        raise ValueError(f"Composition with id={comp_id} not found")

    if not layer_ids:
        raise ValueError("No layers specified for precompose")

    # Read comp properties from cdta
    cdta = comp_cl.find("cdta")
    cdta_data = cdta.data
    width = struct.unpack(">H", cdta_data[140:142])[0]
    height = struct.unpack(">H", cdta_data[142:144])[0]
    duration_num, duration_den = _read_comp_duration(comp_cl)

    # Find the insertion position (position of first selected layer)
    first_pos = None
    for layer_id in layer_ids:
        pos = _find_layer_block_start(comp_cl, layer_id)
        if pos is not None:
            if first_pos is None or pos < first_pos:
                first_pos = pos

    # Extract the selected layer blocks
    extracted_blocks: list[list[Chunk]] = []
    for layer_id in layer_ids:
        start = _find_layer_block_start(comp_cl, layer_id)
        if start is None:
            raise ValueError(f"Layer with id={layer_id} not found")
        block = comp_cl.children[start:start + _LAYER_BLOCK_SIZE]
        extracted_blocks.append(block)

    # Remove selected layers from original comp (reverse order to preserve indices)
    for layer_id in reversed(layer_ids):
        start = _find_layer_block_start(comp_cl, layer_id)
        if start is not None:
            del comp_cl.children[start:start + _LAYER_BLOCK_SIZE]

    # Create a new composition by deep-copying the source comp Item
    fold = root.list.find("Fold")
    source_comp_item = None
    for c in fold.list.children:
        if c.name == "Item":
            idta = c.list.find_optional("idta")
            if idta and isinstance(idta.data, bytes) and len(idta.data) >= 20:
                if struct.unpack(">H", idta.data[0:2])[0] == 4:
                    iid = struct.unpack(">I", idta.data[16:20])[0]
                    if iid == comp_id:
                        source_comp_item = c
                        break

    if source_comp_item is None:
        raise ValueError("Source composition Item not found")

    new_comp = _deep_copy_chunk(source_comp_item)
    next_id = _scan_max_id(root) + 1
    new_comp_id = next_id
    next_id += 1

    # Update new comp IDs
    _set_chunk_id(new_comp.list.find("iide"), "iide", new_comp_id)
    _set_chunk_id(new_comp.list.find("idta"), "idta_id", new_comp_id)

    # Set new comp name
    utf8 = new_comp.list.find("Utf8")
    utf8.data = new_comp_name
    utf8.length = len(new_comp_name.encode("utf-8"))

    # Remove all user Layr blocks from new comp (keep system layers DLay/SLay/CLay/SecL)
    new_comp_cl = new_comp.list
    while True:
        found = False
        for i, c in enumerate(new_comp_cl.children):
            if c.name == "Layr":
                del new_comp_cl.children[i:i + _LAYER_BLOCK_SIZE]
                found = True
                break
        if not found:
            break

    # Insert extracted layers into new comp (before DLay)
    dlay_idx = _find_dlay_index(new_comp_cl)
    insert_at = dlay_idx
    for block in extracted_blocks:
        for i, chunk in enumerate(block):
            new_comp_cl.children.insert(insert_at + i, chunk)
        insert_at += _LAYER_BLOCK_SIZE

    # Add new comp + FEE + view state to Fold
    fold.list.children.append(new_comp)
    # FEE (font/expression engine)
    ppSn_data = b"\x40\x62\xc0\x00\x00\x00\x00\x00"  # default ppSn
    fee = Chunk("LIST", 0, ChunkList("FEE ", [
        Chunk("ppSn", 8, ppSn_data),
    ]))
    fold.list.children.append(fee)
    # Fold-level view state (7 chunks)
    for vc in _build_view_state_block_simple():
        fold.list.children.append(vc)

    # Add precomp layer in original comp at the first layer's position
    precomp_layer_id = _add_layer_from_template(
        root, comp_id, "layr_precomp", new_comp_name, big_endian,
        asset_id=new_comp_id, index=None)

    # Move the precomp layer to the original position
    comp_cl = find_comp_chunklist(root, comp_id, big_endian)
    precomp_start = _find_layer_block_start(comp_cl, precomp_layer_id)
    if precomp_start is not None and first_pos is not None:
        block = comp_cl.children[precomp_start:precomp_start + _LAYER_BLOCK_SIZE]
        del comp_cl.children[precomp_start:precomp_start + _LAYER_BLOCK_SIZE]
        # Recalculate position
        target_pos = _layer_insert_point(comp_cl, 1)
        # Find correct position based on remaining layers
        current_count = _count_user_layers(comp_cl)
        # Insert at beginning for now (user can move later)
        for i, chunk in enumerate(block):
            comp_cl.children.insert(target_pos + i, chunk)

    return new_comp_id, precomp_layer_id


def remove_layer(root: Chunk, comp_id: int, layer_id: int,
                 big_endian: bool) -> bool:
    """Remove a layer from a composition. Returns True if removed."""
    comp_cl = find_comp_chunklist(root, comp_id, big_endian)
    if comp_cl is None:
        return False

    start = _find_layer_block_start(comp_cl, layer_id)
    if start is None:
        return False

    del comp_cl.children[start:start + _LAYER_BLOCK_SIZE]
    return True


def duplicate_layer(root: Chunk, comp_id: int, layer_id: int,
                    big_endian: bool) -> int:
    """Duplicate a layer. Returns the new layer_id."""
    comp_cl = find_comp_chunklist(root, comp_id, big_endian)
    if comp_cl is None:
        raise ValueError(f"Composition with id={comp_id} not found")

    start = _find_layer_block_start(comp_cl, layer_id)
    if start is None:
        raise ValueError(f"Layer with id={layer_id} not found")

    new_layer_id = _scan_max_id(root) + 1

    # Deep copy the entire 16-chunk block
    block = []
    for i in range(start, start + _LAYER_BLOCK_SIZE):
        block.append(_deep_copy_chunk(comp_cl.children[i]))

    # Update layer_id in ldta
    new_layr = block[0]
    ldta = new_layr.data.find("ldta")
    _set_chunk_id(ldta, "ldta_layer_id", new_layer_id)

    # Update ewin layer_id
    ewst = block[1]  # Ewst
    ewin = ewst.data.find_optional("ewin")
    if ewin:
        _set_chunk_id(ewin, "ewin_layer_id", new_layer_id)

    # Insert after the original block
    insert_at = start + _LAYER_BLOCK_SIZE
    for i, chunk in enumerate(block):
        comp_cl.children.insert(insert_at + i, chunk)

    return new_layer_id


def move_layer(root: Chunk, comp_id: int, layer_id: int,
               new_index: int, big_endian: bool) -> None:
    """Move a layer to a new position (1-based index)."""
    comp_cl = find_comp_chunklist(root, comp_id, big_endian)
    if comp_cl is None:
        raise ValueError(f"Composition with id={comp_id} not found")

    start = _find_layer_block_start(comp_cl, layer_id)
    if start is None:
        raise ValueError(f"Layer with id={layer_id} not found")

    # Extract block
    block = comp_cl.children[start:start + _LAYER_BLOCK_SIZE]
    del comp_cl.children[start:start + _LAYER_BLOCK_SIZE]

    # Reinsert
    insert_at = _layer_insert_point(comp_cl, new_index)
    for i, chunk in enumerate(block):
        comp_cl.children.insert(insert_at + i, chunk)
