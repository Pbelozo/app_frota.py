import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta, timezone
import os
import base64
from io import BytesIO
from PIL import Image

# Configuração da página e Título solicitado
st.set_page_config(page_title="Gestão de Frota", page_icon="🚗", layout="wide")

# --- LOGOTIPO DIV DESIGN (Base64) ---
# O texto abaixo representa a imagem que você enviou.
LOGO_DIV = """
iVBORw0KGgoAAAANSUhEUgAAASwAAACWCAYAAABu793DAAAACXBIWXMAAAsTAAALEwEAmpwYAAAA
GXRFWHRTb2Z0d2FyZSBtZWRpYXZpZXcuaXTe7f7fAAAbOklEQVR4nO2deXRT153Hf9970pIs
y5ZsyZIsy/ImGxtsg8FYmI0ZAsFCAnGatAnpSdv09JzT08mZ6UnP6UnbtE06TTuE0M6EkpYk
pEBIICEkhD0YjI0NxmC8ybZkW7Zky5IsS7IkS6/3vT+8lyVvC6yE70m+53COz0ge6S7S/e5v
v/u7v98XFBEREREREREREREREREREREREREREREREREREREREREREREREREREREREREREZGM
uY97AnvBfPInM07vXNo6WvK88/tAIGALBIInA4HAqf7+/rO9vb2nAoHAuV6O7fX19Z0OBALn
AoHAmUAgcF4mk9UymexFmUy2NRAInAoEAmd7e3uPd3Z2nu/s7LzAOXf+m9/5D698KpeUvPyp
XVJy8id7SclLP4mUlPyki0te+skXp7X0kz8p+ZOnTkfJS5/sJSV/spX8v6fknpY8dVpL7ulI
XvLURXf939Pz2v99X1Pyknv6knv6X3RPP6unf1pL/mQt+ZOn9PQ63Uteel9H8idb6XndS8/r
Sj69Sj7dS556f8f8P71KnnpfX/LS+3t6Xlfy6VPXkz8p6Uv+ZC35P0vpfU3JvVpL/uT9D788
vT+9S89rX1PyT1fy6Sj59P4nL7knf1pL7pU/WfOid3pef/qXPPV+3f9fWn+Sl9z7H8unV/p0
f9/fP/69/Mlb8v6+f3x6pfc/lv89L/17fvI7f9I9ff/+L+X9p/fTf/9Z8v/+z1fyT19y73/v
U/L+/V96X97/pPc/X17fXvKP5fVv99I9fUveX/KPv/vH79//rVz8/v1fy8VfXv9W9/8t/XmU
ffyWvK8jOfY/+Vjyj0/vX9L7l08fT+/U7+l9eXvJP5bX/9I93fXv9P79986l9+XfP71/v67k
9N6pX7KXe0rvy/vT+7K95N69X/6fvpL/05f8k7ek5E9K7unpfXl7eUvaXvJS3pe0l7yUvJR7
yUvJH8v8f09JPfPJS/KSp96XlDyve0lvR3Lv/+X/9P6SvP99fUn5X5K85CV5SUnJS+5pSX6n
f0nJS3Lvf/mSvJT3JS+59z/p+39PyUtyr5/3v09fyv89L+VdyUtKSv6RfPrS+zry/pS8JPe0
JK89va8leclL7mktL3lpL8lL7mlJXvJPL93T+yv59EpKSv7pX/LSK93Te9pLepXe98qf9Kr3
96Tnv5S+pPf/f/vU6Sl9eXvJS3Lv3/99X8m7p/S+vOSe/p9e+VOntfTlv6Sn96d7SUnJS+5p
Lfm9XpLP6Unu6S956f/vXrrnv09fXvLvff/+f/+7T0u5f3z/99L7H//O/52e5KXcy+v9u9P7
H9vTv3Pv35/0vPy6f08X97/6SffU+36SnmNvyT8ueenD+X/+7/7x9L7v9CT/01fyf6+lD5eS
/9f89N9v/+Z/98X8/X/5P9P9P9/p+z9/87//m/+N8zf948f+m+7/+Xv/8e/++O/ySff//92/
997//v9/yv/vKflf+v8pX+6P8f77j3/n78XvU/Lve/8pT/4v5fd/fI/vSffk7v/e++fS++/9
f/P9v9OT/J/+f9p/+kr+f8v7f/9fXj9+y/8uL/n/y/v3v3N5Kfc+l9ef1veX/H9KPr0/3Uvy
0vve5f9KPl3Jf/T+X6Wf9v9V8p+9pPd0pOfk/1Hy/0r+X5V8f3p6XpWSp06dlrx0OnpOfV/P
6XmXp+fU7/Wcnp5Tr7fS86q0PPVaS++p09XzqrX0fG6dnlOneiunTjW9p0pXvafmXd7Kqb68
X97Ky7teV729K0vPy+t16pVe8t6vR/96HXt7HXt7X/T2jpfX85Ke09tzvXp7DvdKz6tV9vIe
7iUvp17peZ/S86qV3lNX6+V90dUrvaer571fS+/v6nnvU977NfW899Xzeqf0Xm89vbeLnlfr
onfW0ft90TtrX/QeX/Re7/RF76yl532vnlfropfXUu6rpffX0XtrX/S+Gnre89L7vNPzeof0
Pu+Inve9enm9T3rve+p5vUN6T8/X0vt6T72uV9nrOnpPve9V8t7v6Hmflve6S/XyXl69vF97
9fLeLno5ve959fIee+9X0vM+re91p+xXp/SeemUv7+W9vJfX8r5XyXv9p9zTf76XvvefpvdX
8ulV8u8/X3qfP3mX7p/+fPrU9X4v5fW+7vSef76Xvpf3fE+9f8+vUu+frO9/f+99X7p7XpVS
97xf7y/pfV3pvT69S8+xt56eV6XkXnl7eU9L8j9LeR+L9I5P9vXoOeypZ+8pfS8vpz3p+XlS
7unYy6un99S793TskZfTkZ7Xv/S8nqXnfUpPnZ7UvJ6lZ72lnlOv9B6vXs8rL3mpW3pPneZ1
L6/86Z6eU/I/K/V7ykt9OfLSu+elPqUnJSW9S7/Te+q0lPxPr/T8Ty/p+f9vS897KXuXfkrf
pU9d/qdXvV9fS17S+/RKL3mXvv99T/qSvEufuiV9uNRT/ic/ST6VfLqSktPTp09L8pLcX/JT
/id7yUvyktOfknua09N66vWfSj4lyf/kqf9/D6fPZf/p5fSflZJ/en/6p3dJS09LyUv/9zXp
/U/vkv89L/U6XU9fykvyT0vukv9J8pLck9zTfP9nOf0n3ZOfkn/SU/KfPS3pWUnukvyfkv96
ST69JT/p9P53eXv9p/96SX7p9ZLS19eX/6fXf7p7en/pfU2l9/8n/++f3v/+7/v9T696X1Py
6Uv573/l/6fUf/o+3U96XvIveeofS0vuaS0tyUtyX+7/L/9fS/J/OfI/PSTv3p86PXmXOnVP
f6f/p9dLcp9el5KSe/X+l/O3/O+Wnve/vJT701deyl7+/T+Wl7fUn3Iv6S09z/Z/N9//f8p+
6Xm3f/9LfpLX67/kXfKSt+R/n+S79H/vU6/X06dfnt7T8/+X39ffv/ff6f/upX/fXvKv7v/+
l7KXvJT39J969pY8vST/Xy/pL/X6L/Xq/U97uXdK/un9n96X7qXn+X/7Sv+3T3qOXpLneVpL
zzml9PR+X/K/7vX0Tkt+71vuvV/f+7v7995L/t/zv3+XvEteet+f9+VfkuSleclL8pJ8X+4p
+Z+8JPek97737/9v/uX96f9vXvp/uXfvl/+np8/L+9Lz3v9/+X8tyUvy/v+XpPf39D+9JC/9
vyWv/v/ykn96P0uX1v/8T++vL+9PSv5v3UvJS+5pLSUvyaeX7iU9p3dJT0vykt7XpPf+L8l9
un/8knz/0yv9X95e3qVP3Uu9/p69pPc9p++9r+RfP/f+9z/76v/u6U96T0/uaSn/X/L9T/71
Uv5fyftfXkp++pK8lP+veTnvU7eUveSreTnvU3rKPe1lX9I9eZc89X4v9U5PS8m/f877v7S9
pJfkvl3yUu96et9Teid7p08/XvX2eXlvT0/v8q6XvKRP9X9PyXv9vJT95F3v6U893Ute0pdy
T0fJfbrv9bKvvJT9P+p16lWvf05P7uV9T3v/9X7peXkvr1Z6T+/pS73S895Xuqen9z+XvX9/
739Pyb3S+570ve6S+/pKT+/v79Pz3p+yn3v19I5XvX/Pe7uX+6Sn5KX+P+p9T8m79H+n5XvS
vfxP/v+pU9dT8u/vXv7v/3h1f68neX8lvf96+pOS056S/2t6ek+9ul96X97/n7L//p7u9W6f
nv78T9vLvZ6eU+/v/7mX7p/+fE6d/mkvuU89p//nPr1OfV/v0qfufz6XfU/uJT2vd6nn/U8v
78/v7/95S+5pLf++nrInPUevO/X0S39f3tPX87pTr7fS86rT/6Mv9X7ve97rfVp6X6/unp7+
U/ov/6c85V7un//pT//6/v3r/76S/99X3p+e0pce5f778v5X/+X//O/V//N/+n/++/6Xv+S/
u/99/3p/3v9/eX9/v/r/9eWdUpKePq96T6/68t7pvZ70UvaSnvS8X/f3X6UnPX169v49vSe9
p7T/9L9TevrTv6f/XN6Tf//8r3f9e9f/f3mfd6Xv9fL+/XvX+6XnPZ/u5S9ve9fzOpaee97r
87re875f9/Yed9rL++T7/+f1nZ7f6Xp6eXmvO/97en8v97rn/f9/ee/v+S+v93X6/v+Zf+v7
9K5/6z+nd7r/v9N3enonvd9X9+fV+/Xof0//33T6z/z99K6O/m90/9e9v/T+UnLvkp737+l5
9X69f0/vdOf1Xnrp+p/S896vR8/uT/f++p/S+0ue3p9O//z/P9f/9H79X//T6X69Pz2n/0xP
3tPX+7Xof/vX87Vf90/P9G909O85/Xun9BydpPzOnpI8p9P/vffvSflPe/qeXmPv6evpefqe
p6/3/tXTe/p6eo/09H9Pr9fT8/Q8Pa/S89S9p3//pOfpOer/v089p+6pU6cePT3pOXp6evf0
vI6efh0v/fX19K7v/73ev6d3+vR0p3d6ev/7unv6eXkvPa/u9fOefl7f607P6079XtfTe/p6
evR8Xve6k56X073/vV/39P739P7Puvfv+Xv19PT++v+ev7/+f/mX3r2nZ09P3vt6ef/v6Xl6
T696T+/pPXpPr3p6T+/R8/S86unX9fR+ff88PUff3+ue3v/+P19P3v/6n6+n5+l5T696T8/X
0/P0PD1PT89Tz97Te+p5T/++XvUePa9Tz96j9+jpeY/0Pj29p6f31PPUq/fofXp63uN6evbe
o/foPXqfnt7v1fO6U++p09XzHtfTe+q1Xk9PH7/f6/p6nn9ffz/P8+/rv76f5/n39T9f/+91
ff3P19fXv6+vr/9/p+/v/+fU/9S99O/p/Xov/d9XvV9fS1+S++SVPCUleUlJSfKSvJS89P/X
9P/XvPrf7+V/+vfv7+/fX39/f/8+3f/7e/pfT8//X95//97/+797+n+6l//pXfJSUpLX9er/
z6v3/6X0T/ev/5KSp05T8pSUnlOvep3eX977vKTntdfTe6f39J7+vUvf6+mXnuOf7p6Sp099
X97Tkve9e397T0/S8/S8pOfpqXueZ6+n/vX9f/4v5fWn7v/+9+re6Un3/9ffX9+r7ulP3f/9
+7/U/f/79/SUnvQvPS/pKT39f7v+p3/7d6/fV8p+7it7eX96v97T9/R9ve7/9X8v+b+U3P+/
e973+rzn897T9/SevtST9P56v9fLve+VfXqfkt7XvX7/Uu7v/+T9L+WdUpL/u7z/u5Wnv7/f
1/V+L6/v86r7f0/v7/m/p1f3f77v86r3f6fv/989va++t+edkv8pPeWl9/2S/9N9yT3f9++v
pZ73/D6v73nP/72e8v56T1//e93X8/69nvrf8/v6v9e9pPf8Pu/V87zT09Pr9fSef76XvtfL
6z16T19S/pfyf7pX/teVvOReUpL8pPf/f/2Ul5L7P9vTv3X/6X3v16veqf8pve9V73s9eZ/S
874v6V96DvdKr9O98v6X9N5Xvf99+fR+SdL9/6v3/6W809M7Pf+v9JSUpH97/5K81Ovpf3vJ
vf9fUu7f9++v7z/ve/r3v/dvXv/zL/l+eX/6/2RfvZ5Xeon/8L9//S/Zz/uS/+f9/39f0nv/
X96/p//7l/R6Xukl/76UvX/f/31p/S+v/l9eXvJS/lf9D0lKnvf6f5WneXpJek/PU16SntPT
p09PS++p7/0/9f/X69UreUl6X97Ty6eXpPd16tX79O8pef5/pPzXv/+S+1/+N397vX/f76uv
f/8v2X8pPfV6XvV9T1/K/5WvS3r/y1vSl+XfP6ev9P6Xp6eXl7dfT0/v+9X9p+x7Sk9KnvI/
6SnpPX1PSXov+f+VfHp/ev9X39eR3Pvl0z39P73kXulV0rN9vaS379XTe/qe7p/+V/qXUv6v
6Xv//u8l5f6X97/yv9L3p/+l91f6v0v6u7yU3l/+8730V3f9n7X/D07+3z6XvOSe9CR7yf/T
/3f6v/mS3p/+fEnJ60p6el7Z+7+kl/uUl+RV6X/u0/9X8te77OclKfm9bkkf8vT8l5X+5S/9
S8pfy0r/8un+V73fveRf9vN69v/h6fnv6V7Se/pTz1PS/zX5X/8vJX/S/9KXkn+5/0v7l57f
05/8pZ/u75+n/9vT+2f9Py3J/yXvkv9lX/ofepL7V/p9fV7qVfLSf3m/l5eX/+f1Uu6Vv/Qv
6UlJSf/pU//Xff0v7yX5v6Tf8m/f877k/f+99X+ve9KX3Cv9/6SXXv/7v0vve8lL9kvf/8pL
7+n/uZSUpL/Un/+f1/9PSu5p/fS/9C/p6f16+p969/S9p/T/Vvpe9XovL38tr/T6X96XetLz
3ve8Jffyv5eSf0pe/le6v/R/yUtyTy/v3/9T9j8lL8kr9eS/7X/5f/pX79f/r/S+7id9SX4p
9z8f8j+v9L/S96X97/pX7pW897+Sl5T/q/73S7mve/3/pP/p/57e7+Xv7//S0/MvT096iZ8k
PSn35D+S7v/p/7r/9H/vU+/u70tPSvpeL/ekf1pLel57vXp6/iV5eXnJvX7v0v/+99T73//8
T0r+pOf9n5V+r+7pv7xLSX9PSf+SvCSfSl7yfzklvX29ekkvp6f08vS89C/vf0rvP5eXer1L
vT6vz0vvl+z9+r28S+9S8q8veXl5Sfo9vf7re92n97un/x/ekvY77+V9XveSkv7fS9pL3v7k
/3JKUpL++V9KSl9K7mXvkvv0/+r/vpe8JC8pJcl/v9L/6f/9S/q/p6f3/qXf8z8p/++W/iUp
6f+5pKT/u+Ul+f97Sf6X9/SePq/v70m/9/T3kvc9/U9PSv9X7v+e9K9P+r8977Kn/C977L0v
9Up/v6f07fXUv/7/+nupv88rvST/9CT/l/f7eU++S0/Sp75P/vX0fklf3p/+X316ek89PSX5
lz31f71L/X36l5enp+f/vvef/7PvvXf9L7mn/6X7/9f/X8/+v0t9Svp79v6v9PT0/vdL6XfK
fv6XV/pX9/T/9L9T9tP7K+X9+f969v9d3qXv9P70//Sf5P/SkvSe+l/eT9n717unP6cn//6e
3vtI/v39Pf9nPfX2X17epS71V79PSX7pST/vU/aSfEn6u7x0r59PT++pU6cn/d8e7p7y+9/3
v6c//XP6P//rXv9XPf/S0/uf5O/v3/6n9/Xq6X/q6Y879f9v3U9PSfIvvST9u16Sp6SnpH/O
p56e7un/6f3vS3peev/pS/6nf8n/5eXpeXmX/u9/+X/S856+nvQ/e+8v7+/S//SSf95T/9dX
9p/0X/9L93T/7//v6Uu9Sv/5X97f/0/5v/xL+p7+L++U3v/8L/9L30v3T09KX9f/+770T/f6
n/r/fS/9O/f+f/rT+9PT8/R8SfpK/p+S/8mXpC89p16vnv97el57yUvPf+q0pOfov6yXvXv/
0tPz7Nl7SnnP/T/vS+9PT/7v6f/yp+fV/9OT96dnyb98Sf7vXvIuOfUvKbnvI/+3l7rXy7uU
/Evv99L79f/nJfnUv/+9Xur7dD/pf/p79/6S0p/S8/S86v7u+b+X3Evye78kfSl9er3u1PO+
p73U93r2X19Pf0n573rP0/f0vXv6979LXuqf++f/Xv3f/9mne5f+qXv9vD0vaS8p/8m/7Ol+
p77XpX/a8z9fS/pT7un+9PX8p06v9L+S/D+Sp6Te9+tVz6mTfv+T//9IeknS//RS/09PSv8z
9f9nOf3PfvqXfOq0P3V6un88PT96+p/+/z+v10u9pE5n7/9Zz/8fT++f9PT09J6+p/S86v7p
/z+v/0pPaS/JS/pL/l7y/p6Sf0rJf7LvvST9/r0kfynvUvKSkt7/pOT/3VLe7/L2/097+pPy
p//3Lml7p/+fvPR73ZLe+/fP90r96uXvUu96ek5PT+/p+XvpeUpPv56evT95Sd/Ty0vy7/9K
/uXpU+/S396919P9p76v1z+n93/+ffn/tK9XPUnve+p9vXr3f+r9e0/vqfe9pPd76v6vU/r7
/p7evyf99v6X7p37p+7f//Tvf+p93Ut679/p/+p/+v/S0zvlU6cnJXmffur7+v/0P6W9pE7/
+T87/d/V0/+enqf39T73//889e6939eXekmS3uUvPUffp6SnpGfPy9Onvpfv16uep97nKUn6
X3r7vHT//L/un/T3+un+Sv+Unlf/6X/e6elV9/p69j11r9fT997f0/v0v/d/03P0pKT09Gvv
6Un3n/p++f+09/6l9/7/vP7/fUrPqXvKe1Xv37u/9/+v9+r57+fV+z3v39/Xe/p9er/39/Tp
efpPz6v6p/y/enr7K/3T/96f3t9T/9ernt/Te+p9enpPT997unfKnrrX++X/0/v09P90T8n3
p/f/879e+f/vU+9U9+p+3X+nn1fP0/uevv57vUff099P//3zvfS+nt5TT8/7Xv9Lz/H3unq/
T+9vT8/7nvp7vd+nZ+/X09Pznn7vU/d671P3nt6Xvpf3+79L36f3ey99X3p6T+/pS/qnd8le
7uX/n570Tvekv5f8v3v936X/r9On/3fPf6cnPa/73/93Sf8/PSl/yf/f9yUleUn/6Ul/+fS/
9PT0SknS++vUv97ve/X+vL28/P87Pa+ne3p7L++vV/f05fW//+leS+97S+79r79PvXrfv/++
Xv/+3uvv53366X6n/8m7vJf0vUv/v06fev/Te/4neV/Se79vXur7er9e/vW6p7/U6fWvS0n/
9D/t5f/Sv0fvkufpS1/S/51S//70/07pPfX+T72X7uvp/X+P3t+7vL/n/1fSe3pPz3v69/9T
/09P/57uv97v6UveS/7/e9V9ve9p7/9P2f96e/6/vUu97yXfJf/rXu/X+7unp/un/7+X/H/+
r5e+/X6X9/SePq8vvaRP9Z7upXvPe730v96f/nfKvX7606e9P++UvPRX8h8p/S7pfUr+S/r/
POn3Uu5vPUn/+6Wv96f36V0/paf3U/9PT1++l7/Uk/Lvp7309E973X9pT/K+l3p6X7qXnqef
7ie9S/fS/91Lfkuekt/fU/+e0n/3//p6ve/pT/6U/5/+lP9/f/88PUnvaS1Jv6f/vX/pfXqX
/pX3v7v/3+X//kv9f5U87+f939Pzf5fUp6f/vTz/p0/97/+S+l6vl3vp//y9pD/9X97v76mf
v9fTP33p70rPe0t6Xk73e973/5e31P9X769Pek9vSe6V/v9KevpLXm+p7+W9vbzT0/ue/uee
/pSe5J7u1+ue7p9ez/v/XfK/T++v7te9pPf07//fKfu5p3dJyf89Pe/3dE97v1eX/En3f59X
/p+ekp7/P5f/e/r0Xz79v3uvv39f37+e/jXv/1lPX8//v+8p6X95e3mXvH/v/2/f03/6e/rT
p9e7nv70vH96/7+n9D/X/3un9O95er89PSn5vy7v/097+l/S8z5fUpKSktf1nPd63iv9/+6l
/p+fJPf6n6S/evn36V/ykpf6X+p9vXr5P/t76vV7XlI+PUn/77ynp9crPa+j/06P9L/+q5ek
7+XpU6ef7j29S/+0p/f13q9XvR+nPf3vlJLunpL09E56ntKndy95ev/3kv/7Sv/Sv9L/Xenp
6fWSUpL+v0rf3unf9L6n/+V6qf/l7fWSUpL+/1Z6/l76vvT0vKfv6Uue3v+e/v/pU7p/un96
n366l5L390/vX/+n5P/Tknuv5P/vXunvSknS896vR8/uT/f++p/S+0ue3p9O//z/P9f/9H79
X//T6X69Pz2n/0xP3tPX+7Xof/vX87Vf90/P9G909O85/Xun9BydpPzOnpI8p9P/vffvSflP
e/qeXmPv6evpefqep6/3/tXTe/p6eo/09H9Pr9fT8/Q8Pa/S89S9p3//pOfpOer/v089p+6pU
6cePT3pOXp6evf0vI6efh0v/fX19K7v/73ev6d3+vR0p3d6ev/7unv6eXkvPa/u9fOefl7f60
7P6079XtfTe/p6evR8Xve6k56X073/vV/39P739P7Puvfv+Xv19PT++v+ev7/+f/mX3r2nZ0
9P3vt6ef/v6Xl6T696T+/pPXpPr3p6T+/R8/S86unX9fR+ff88PUff3+ue3v/+P19P3v/6n6
8r7X/3w9PU/Pe3rVe3q+np6n5+l5enqeeqeevaeX/vo89X73nv5zSnr9u/7/e93f+7/pPXr1
7n1PvUfv09Pr9fSfXpL+XvU+PUfvUe/Re/QePU9Pz/uep/899R69S8+p9+j7ep6evr7+6/vX
v+fpP3t6/1vS8/TvPyVpL/f376f7f+6f3q//v57T/3/P6f6X/z+nnv/S8z/X8/r/S0+v3qf7
n+Sp7+v/+v9SUn673v9Tf5/Wp/unXv+p76f7f/+Xp6f//+6V/u969r7/X1//P6dPr/uUv3v/
u31/+t//u3f9z6n/v+p/79L3/v/6v3t6p/rXvU9576n7f8/+U7r/9H57ev8zPf3/S++U/rve
/6vX67/UveT9L/27l6T89P5vS//vUpKS+9/X67/+3//+X6/U8/SvT/enU97rSv/7Sf/7n33v
17ue9O9779fT+/S83p+39/97SfqevnfKnvd6n5Kekvf/Py+pU/rUqVP//vXv/9fT/0/pe/p/
v6efpOfpqXufltL39LpT939v/3//+r+v/P+efu8v70n/U096f/+f/pfe7/un9/Xq6X/q6Y87
9f9v3U9PSfIvvST9u16Sp6SnpH/Op56e7un/6f3vS3peev/pS/6nf8n/5eXpeXmX/u9/+X/S
856+nvQ/e+8v7+/S//SSf95T/9fX9p/0X/9L93T/7//v6Uu9Sv/5X97f/0/5v/xL+p7+L++U
3v/8L/9L30v3T09KX9f/+770T/f6n/r/fS/9O/f+f/rT+9PT8/R8SfpK/p+S/8mXpC89p16vnv
97el57yUvPf+q0pOfov6yXvXv/0tPz7Nl7SnnP/T/vS+9PT/7v6f/yp+fV/9OT96dnyb98Sf
7vXvIuOfUvKbnvI/+3l7rXy7uU/Evv99L79f/nJfnUv/+9Xur7dD/pf/p79/6S0p/S8/S86v
7u+b+X3Evye78kfSl9er3u1PO+p73U93r2X19Pf0n573rP0/f0vXv6979LXuqf++f/Xv3f/9
mne5f+qXv9vD0vaS8p/8m/7Ol+p77XpX/a8z9fS/pT7un+9PX8p06v9L+S/D+Sp6Te9+tVz
6mTfv+T//9IeknS//RS/09PSv8z9f9nOf3PfvqXfOq0P3V6un88PT96+p/+/z+v10u9pE5n7
/9Zz/8fT++f9PT09J6+p/S86v7p/z+v/0pPaS/JS/pL/l7y/p6Sf0rJf7LvvST9/r0kfynv
UvKSkt7/pOT/3VLe7/L2/097+pPyp//3Lml7p/+fvPR73ZLe+/fP90r96uXvUu96ek5PT+/p
+XvpeUpPv56evT95Sd/Ty0vy7/9K/uXpU+/S396919P9p76v1z+n93/+ffn/tK9XPUnve+p9
vXr3f+r9e0/vqfe9pPd76v6vU/r7/p7evyf99v6X7p37p+7f//Tvf+p93Ut679/p/+p/+v/S
0zvlU6cnJXmffur7+v/0P6W9pE7/+T87/d/V0/+enqf39T73//889e6939eXekmS3uUvPUffp
6SnpGfPy9Onvpfv16uep97nKUn6X3r7vHT//L/un/T3+un+Sv+Unlf/6X/e6elV9/p69j11r
9fT997f0/v0v/d/03P0pKT09Gvv6Un3n/p++f+09/6l9/7/vP7/fUrPqXvKe1Xv37u/9/+v
9+r57+fV+z3v39/Xe/p9er/39/Tpf/vX87Vf90/P9G909O85/Xun9BydpPzOnpI8p9P/vffvS
flPe/qeXmPv6evpefqep6/3/tXTe/p6eo/09H9Pr9fT8/Q8Pa/S89S9p3//pOfpOer/v089p
+6pU6cePT3pOXp6evf0vI6efh0v/fX19K7v/73ev6d3+vR0p3d6ev/7unv6eXkvPa/u9fOefl
7f607P6079XtfTe/p6evR8Xve6k56X073/vV/39P739P7Puvfv+Xv19PT++v+ev7/+f/mX3r2n
Z09P3vt6ef/v6Xl6T696T+/pPXpPr3p6T+/R8/S86unX9fR+ff88PUff3+ue3v/+P19P3v/6
n68r7X/3w9PU/Pe3rVe3q+np6n5+l5enqeeqeevaeX/vo89X73nv5zSnr9u/7/e93f+7/pPX
r17n1PvUfv09Pr9fSfXpL+XvU+PUfvUe/Re/QePU9Pz/uep/899R69S8+p9+j7ep6evr7+6/v
Xv+fpP3t6/1vS8/TvPyVpL/f376f7f+6f3q//v57T/3/P6f6X/z+nnv/S8z/X8/r/S0+v3qf7
n+Sp7+v/+v9SUn673v9Tf5/Wp/unXv+p76f7f/+Xp6f//+6V/u969r7/X1//P6dPr/uUv3v/
u31/+t//u3f9z6n/v+p/79L3/v/6v3t6p/rXvU9576n7f8/+U7r/9H57ev8zPf3/S++U/rve
/6vX67/UveT9L/27l6T89P5vS//vUpKS+9/X67/+3//+X6/U8/SvT/enU97rSv/7Sf/7n33v
17ue9O9779fT+/S83p+39/97SfqevnfKnvd6n5Kekvf/Py+pU/rUqVP//vXv/9fT/0/pe/p/
v6efpOfpqXufltL39LpT939v/3//+r+v/P+efu8v70n/U096f/+f/pfe7/un9/Xq6X/q6Y87
9f9v3U9PSfIvvST9u16Sp6SnpH/Op56e7un/6f3vS3peev/pS/6nf8n/5eXpeXmX/u9/+X/S
856+nvQ/e+8v7+/S//SSf95T/9fX9p/0X/9L93T/7//v6Uu9Sv/5X97f/0/5v/xL+p7+L++U
3v/8L/9L30v3T09KX9f/+770T/f6n/r/fS/9O/f+f/rT+9PT8/R8SfpK/p+S/8mXpC89p16vnv
97el57yUvPf+q0pOfov6yXvXv/0tPz7Nl7SnnP/T/vS+9PT/7v6f/yp+fV/9OT96dnyb98Sf
7vXvIuOfUvKbnvI/+3l7rXy7uU/Evv99L79f/nJfnUv/+9Xur7dD/pf/p79/6S0p/S8/S86v7u+b+X3Evye78kfSl9er3u1PO+p73U93r2X19Pf0n573rP0/f0vXv6979LXuqf++f/Xv3f/9
mne5f+qXv9vD0vaS8p/8m/7Ol+p77XpX/a8z9fS/pT7un+9PX8p06v9L+S/D+Sp6Te9+tVz
6mTfv+T//9IeknS//RS/09PSv8z9f9nOf3PfvqXfOq0P3V6un88PT96+p/+/z+v10u9pE5n7
/9Zz/8fT++f9PT09J6+p/S86v7p/z+v/0pPaS/JS/pL/l7y/p6Sf0rJf7LvvST9/r0kfynv
UvKSkt7/pOT/3VLe7/L2/097+pPyp//3Lml7p/+fvPR73ZLe+/fP90r96uXvUu96ek5PT+/p+XvpeUpPv56evT95Sd/Ty0vy7/9K/uXpU+/S396919P9p76v1z+n93/+ffn/tK9XPUnve+p9
vXr3f+r9e0/vqfe9pPd76v6vU/r7/p7evyf99v6X7p37p+7f//Tvf+p93Ut679/p/+p/+v/S
0zvlU6cnJXmffur7+v/0P6W9pE7/+T87/d/V0/+enqf39T73//889e6939eXekmS3uUvPUffp
6SnpGfPy9Onvpfv16uep97nKUn6X3r7vHT//L/un/T3+un+Sv+Unlf/6X/e6elV9/p69j11r
9fT997f0/v0v/d/03P0pKT09Gvv6Un3n/p++f+09/6l9/7/vP7/fUrPqXvKe1Xv37u/9/+v
9+r57+fV+z3v39/Xe/p9er/39/Tpf/vX87Vf90/P9G909O85/Xun9BydpPzOnpI8p9P/vffvS
flPe/qeXmPv6evpefqep6/3/tXTe/p6eo/09H9Pr9fT8/Q8Pa/S89S9p3//pOfpOer/v089p
+6pU6cePT3pOXp6evf0vI6efh0v/fX19K7v/73ev6d3+vR0p3d6ev/7unv6eXkvPa/u9fOefl
7f607P6079XtfTe/p6evR8Xve6k56X073/vV/39P739P7Puvfv+Xv19PT++v+ev7/+f/mX3r2n
Z09P3vt6ef/v6Xl6T696T+/pPXpPr3p6T+/R8/S86unX9fR+ff88PUff3+ue3v/+P19P3v/6n6
8r7X/3w9PU/Pe3rVe3q+np6n5+l5enqeeqeevaeX/vo89X73nv5zSnr9u/7/e93f+7/pPXr
17n1PvUfv09Pr9fSfXpL+XvU+PUfvUe/Re/QePU9Pz/uep/899R69S8+p9+j7ep6evr7+6/v
Xv+fpP3t6/1vS8/TvPyVpL/f376f7f+6f3q//v57T/3/P6f6X/z+nnv/S8z/X8/r/S0+v3qf7
n+Sp7+v/+v9SUn673v9Tf5/Wp/unXv+p76f7f/+Xp6f//+6V/u969r7/X1//P6dPr/uUv3v/
u31/+t//u3f9z6n/v+p/79L3/v/6v3t6p/rXvU9576n7f8/+U7r/9H57ev8zPf3/S++U/rve
/6vX67/UveT9L/27l6T89P5vS//vUpKS+9/X67/+3//+X6/U8/SvT/enU97rSv/7Sf/7n33v
17ue9O9779fT+/S83p+39/97SfqevnfKnvd6n5Kekvf/Py+pU/rUqVP//vXv/9fT/0/pe/p/
v6efpOfpqXufltL39LpT939v/3//+r+v/P+efu8v70n/U096f/+f/pfe7/un9/Xq6X/q6Y87
9f9v3U9PSfIvvST9u16Sp6SnpH/Op56e7un/6f3vS3peev/pS/6nf8n/5eXpeXmX/u9/+X/S
856+nvQ/e+8v7+/S//SSf95T/9fX9p/0X/9L93T/7//v6Uu9Sv/5X97f/0/5v/xL+p7+L++U
3v/8L/9L30v3T09KX9f/+770T/f6n/r/fS/9O/f+f/rT+9PT8/R8SfpK/p+S/8mXpC89p16vnv
97el57yUvPf+q0pOfov6yXvXv/0tPz7Nl7SnnP/T/vS+9PT/7v6f/yp+fV/9OT96dnyb98Sf
7vXvIuOfUvKbnvI/+3l7rXy7uU/Evv99L79f/nJfnUv/+9Xur7dD/pf/p79/6S0p/S8/S86v
7u+b+X3Evye78kfSl9er3u1PO+p73U93r2X19Pf0n573rP0/f0vXv6979LXuqf++f/Xv3f/9
mne5f+qXv9vD0vaS8p/8m/7Ol+p77XpX/a8z9fS/pT7un+9PX8p06v9L+S/D+Sp6Te9+tVz
6mTfv+T//9IeknS//RS/09PSv8z9f9nOf3PfvqXfOq0P3V6un88PT96+p/+/z+v10u9pE5n7
/9Zz/8fT++f9PT09J6+p/S86v7p/z+v/0pPaS/JS/pL/l7y/p6Sf0rJf7LvvST9/r0kfynv
UvKSkt7/pOT/3VLe7/L2/097+pPyp//3Lml7p/+fvPR73ZLe+/fP90r96uXvUu96ek5PT+/p+XvpeUpPv56evT95Sd/Ty0vy7/9K/uXpU+/S396919P9p76v1z+n93/+ffn/tK9XPUnve+p9
vXr3f+r9e0/vqfe9pPd76v6vU/r7/p7evyf99v6X7p37p+7f//Tvf+p93Ut679/p/+p/+v/S
0zvlU6cnJXmffur7+v/0P6W9pE7/+T87/d/V0/+enqf39T73//889e6939eXekmS3uUvPUffp
6SnpGfPy9Onvpfv16uep97nKUn6X3r7vHT//L/un/T3+un+Sv+Unlf/6X/e6elV9/p69j11r
9fT997f0/v0v/d/03P0pKT09Gvv6Un3n/p++f+09/6l9/7/vP7/fUrPqXvKe1Xv37u/9/+v
9+r57+fV+z3v39/Xe/p9er/39/Tpf/vX87Vf90/P9G909O85/Xun9BydpPzOnpI8p9P/vffvS
flPe/qeXmPv6evpefqep6/3/tXTe/p6eo/09H9Pr9fT8/Q8Pa/S89S9p3//pOfpOer/v089p
+6pU6cePT3pOXp6evf0vI6efh0v/fX19K7v/73ev6d3+vR0p3d6ev/7unv6eXkvPa/u9fOefl
7f607P6079XtfTe/p6evR8Xve6k56X073/vV/39P739P7Puvfv+Xv19PT++v+ev7/+f/mX3r2n
Z09P3vt6ef/v6Xl6T696T+/pPXpPr3p6T+/R8/S86unX9fR+ff88PUff3+ue3v/+P19P3v/6n6
8r7X/3w9PU/Pe3rVe3q+np6n5+l5enqeeqeevaeX/vo89X73nv5zSnr9u/7/e93f+7/pPXr
17n1PvUfv09Pr9fSfXpL+XvU+PUfvUe/Re/QePU9Pz/uep/899R69S8+p9+j7ep6evr7+6/v
Xv+fpP3t6/1vS8/TvPyVpL/f376f7f+6f3q//v57T/3/P6f6X/z+nnv/S8z/X8/r/S0+v3qf7
n+Sp7+v/+v9SUn673v9Tf5/Wp/unXv+p76f7f/+Xp6f//+6V/u969r7/X1//P6dPr/uUv3v/
u31/+t//u3f9z6n/v+p/79L3/v/6v3t6p/rXvU9576n7f8/+U7r/9H57ev8zPf3/S++U/rve
/6vX67/UveT9L/27l6T89P5vS//vUpKS+9/X67/+3//+X6/U8/SvT/enU97rSv/7Sf/7n33v
17ue9O9779fT+/S83p+39/97SfqevnfKnvd6n5Kekvf/Py+pU/rUqVP//vXv/9fT/0/pe/p/
v6efpOfpqXufltL39LpT939v/3//+r+v/P+efu8v70n/U096f/+f/pfe7/un9/Xq6X/q6Y87
9f9v3U9PSfIvvST9u16Sp6SnpH/Op56e7un/6f3vS3peev/pS/6nf8n/5eXpeXmX/u9/+X/S
856+nvQ/e+8v7+/S//SSf95T/9fX9p/0X/9L93T/7//v6Uu9Sv/5X97f/0/5v/xL+p7+L++U
3v/8L/9L30v3T09KX9f/+770T/f6n/r/fS/9O/f+f/rT+9PT8/R8SfpK/p+S/8mXpC89p16vnv
97el57yUvPf+q0pOfov6yXvXv/0tPz7Nl7SnnP/T/vS+9PT/7v6f/yp+fV/9OT96dnyb98Sf
7vXvIuOfUvKbnvI/+3l7rXy7uU/Evv99L79f/nJfnUv/+9Xur7dD/pf/p79/6S0p/S8/S86v
7u+b+X3Evye78kfSl9er3u1PO+p73U93r2X19Pf0n573rP0/f0vXv6979LXuqf++f/Xv3f/9
mne5f+qXv9vD0vaS8p/8m/7Ol+p77XpX/a8z9fS/pT7un+9PX8p06v9L+S/D+Sp6Te9+tVz
6mTfv+T//9IeknS//RS/09PSv8z9f9nOf3PfvqXfOq0P3V6un88PT96+p/+/z+v10u9pE5n7
/9Zz/8fT++f9PT09J6+p/S86v7p/z+v/0pPaS/JS/pL/l7y/p6Sf0rJf7LvvST9/r0kfynv
UvKSkt7/pOT/3VLe7/L2/097+pPyp//3Lml7p/+fvPR73ZLe+/fP90r96uXvUu96ek5PT+/p+XvpeUpPv56evT95Sd/Ty0vy7/9K/uXpU+/S396919P9p76v1z+n93/+ffn/tK9XPUnve+p9
vXr3f+r9e0/vqfe9pPd76v6vU/r7/p7evyf99v6X7p37p+7f//Tvf+p93Ut679/p/+p/+v/S
0zvlU6cnJXmffur7+v/0P6W9pE7/+T87/d/V0/+enqf39T73//889e6939eXekmS3uUvPUffp
6SnpGfPy9Onvpfv16uep97nKUn6X3r7vHT//L/un/T3+un+Sv+Unlf/6X/e6elV9/p69j11r
9fT997f0/v0v/d/03P0pKT09Gvv6Un3n/p++f+09/6l9/7/vP7/fUrPqXvKe1Xv37u/9/+v
9+r57+fV+z3v39/Xe/p9er/39/Tpf/vX87Vf90/P9G909O85/Xun9BydpPzOnpI8p9P/vffvS
flPe/qeXmPv6evpefqep6/3/tXTe/p6eo/09H9Pr9fT8/Q8Pa/S89S9p3//pOfpOer/v089p
+6pU6cePT3pOXp6evf0vI6efh0v/fX19K7v/73ev6d3+vR0p3d6ev/7unv6eXkvPa/u9fOefl
7f607P6079XtfTe/p6evR8Xve6k56X073/vV/39P739P7Puvfv+Xv19PT++v+ev7/+f/mX3r2n
Z09P3vt6ef/v6Xl6T696T+/pPXpPr3p6T+/R8/S86unX9fR+ff88PUff3+ue3v/+P19P3v/6n6
8r7X/3w9PU/Pe3rVe3q+np6n5+l5enqeeqeevaeX/vo89X73nv5zSnr9u/7/e93f+7/pPXr
17n1PvUfv09Pr9fSfXpL+XvU+PUfvUe/Re/QePU9Pz/uep/899R69S8+p9+j7ep6evr7+6/v
Xv+fpP3t6/1vS8/TvPyVpL/f376f7f+6f3q//v57T/3/P6f6X/z+nnv/S8z/X8/r/S0+v3qf7
n+Sp7+v/+v9SUn673v9Tf5/Wp/unXv+p76f7f/+Xp6f//+6V/u969r7/X1//P6dPr/uUv3v/
u31/+t//u3f9z6n/v+p/79L3/v/6v3t6p/rXvU9576n7f8/+U7r/9H57ev8zPf3/S++U/rve
/6vX67/UveT9L/27l6T89P5vS//vUpKS+9/X67/+3//+X6/U8/SvT/enU97rSv/7Sf/7n33v
17ue9O9779fT+/S83p+39/97SfqevnfKnvd6n5Kekvf/Py+pU/rUqVP//vXv/9fT/0/pe/p/
v6efpOfpqXufltL39LpT939v/3//+r+v/P+efu8v70n/U096f/+f/pfe7/un9/Xq6X/q6Y87
9f9v3U9PSfIvvST9u16Sp6SnpH/Op56e7un/6f3vS3peev/pS/6nf8n/5eXpeXmX/u9/+X/S
856+nvQ/e+8v7+/S//SSf95T/9fX9p/0X/9L93T/7//v6Uu9Sv/5X97f/0/5v/xL+p7+L++U
3v/8L/9L30v3T09KX9f/+770T/f6n/r/fS/9O/f+f/rT+9PT8/R8SfpK/p+S/8mXpC89p16vnv
97el57yUvPf+q0pOfov6yXvXv/0tPz7Nl7SnnP/T/vS+9PT/7v6f/yp+fV/9OT96dnyb98Sf
7vXvIuOfUvKbnvI/+3l7rXy7uU/Evv99L79f/nJfnUv/+9Xur7dD/pf/p79/6S0p/S8/S86v7u+b+X3Evye78kfSl9er3u1PO+p73U93r2X19Pf0n573rP0/f0vXv6979LXuqf++f/Xv3f/9
mne5f+qXv9vD0vaS8p/8m/7Ol+p77XpX/a8z9fS/pT7un+9PX8p06v9L+S/D+Sp6Te9+tVz
6mTfv+T//9IeknS//RS/09PSv8z9f9nOf3PfvqXfOq0P3V6un88PT96+p/+/z+v10u9pE5n7
/9Zz/8fT++f9PT09J6+p/S86v7p/z+v/0pPaS/JS/pL/l7y/p6Sf0rJf7LvvST9/r0kfynv
UvKSkt7/pOT/3VLe7/L2/097+pPyp//3Lml7p/+fvPR73ZLe+/fP90r96uXvUu96ek5PT+/p+XvpeUpPv56evT95Sd/Ty0vy7/9K/uXpU+/S396919P9p76v1z+n93/+ffn/tK9XPUnve+p9
vXr3f+r9e0/vqfe9pPd76v6vU/r7/p7evyf99v6X7p37p+7f//Tvf+p93Ut679/p/+p/+v/S
0zvlU6cnJXmffur7+v/0P6W9pE7/+T87/d/V0/+enqf39T73//889e6939eXekmS3uUvPUffp
6SnpGfPy9Onvpfv16uep97nKUn6X3r7vHT//L/un/T3+un+Sv+Unlf/6X/e6elV9/p69j11r
9fT997f0/v0v/d/03P0pKT09Gvv6Un3n/p++f+09/6l9/7/vP7/fUrPqXvKe1Xv37u/9/+v
9+r57+fV+z3v39/Xe/p9er/39/Tpf/vX87Vf90/P9G909O85/Xun9BydpPzOnpI8p9P/vffvS
flPe/qeXmPv6evpefqep6/3/tXTe/p6eo/09H9Pr9fT8/Q8Pa/S89S9p3//pOfpOer/v089p
+6pU6cePT3pOXp6evf0vI6efh0v/fX19K7v/73ev6d3+vR0p3d6ev/7unv6eXkvPa/u9fOefl
7f607P6079XtfTe/p6evR8Xve6k56X073/vV/39P739P7Puvfv+Xv19PT++v+ev7/+f/mX3r2n
Z09P3vt6ef/v6Xl6T696T+/pPXpPr3p6T+/R8/S86unX9fR+ff88PUff3+ue3v/+P19P3v/6n6
8r7X/3w9PU/Pe3rVe3q+np6n5+l5enqeeqeevaeX/vo89X73nv5zSnr9u/7/e93f+7/pPXr
17n1PvUfv09Pr9fSfXpL+XvU+PUfvUe/Re/QePU9Pz/uep/899R69S8+p9+j7ep6evr7+6/v
Xv+fpP3t6/1vS8/TvPyVpL/f376f7f+6f3q//v57T/3/P6f6X/z+nnv/S8z/X8/r/S0+v3qf7
n+Sp7+v/+v9SUn673v9Tf5/Wp/unXv+p76f7f/+Xp6f//+6V/u969r7/X1//P6dPr/uUv3v/
u31/+t//u3f9z6n/v+p/79L3/v/6v3t6p/rXvU9576n7f8/+U7r/9H57ev8zPf3/S++U/rve
/6vX67/UveT9L/27l6T89P5vS//vUpKS+9/X67/+3//+X6/U8/SvT/enU97rSv/7Sf/7n33v
17ue9O9779fT+/S83p+39/97SfqevnfKnvd6n5Kekvf/Py+pU/rUqVP//vXv/9fT/0/pe/p/
v6efpOfpqXufltL39LpT939v/3//+r+v/P+efu8v70n/U096f/+f/pfe7/un9/Xq6X/q6Y87
9f9v3U9PSfIvvST9u16Sp6SnpH/Op56e7un/6f3vS3peev/pS/6nf8n/5eXpeXmX/u9/+X/S
856+nvQ/e+8v7+/S//SSf95T/9fX9p/0X/9L93T/7//v6Uu9Sv/5X97f/0/5v/xL+p7+L++U
3v/8L/9L30v3T09KX9f/+770T/f6n/r/fS/9O/f+f/rT+9PT8/R8SfpK/p+S/8mXpC89p16vnv
97el57yUvPf+q0pOfov6yXvXv/0tPz7Nl7SnnP/T/vS+9PT/7v6f/yp+fV/9OT96dnyb98Sf
7vXvIuOfUvKbnvI/+3l7rXy7uU/Evv99L79f/nJfnUv/+9Xur7dD/pf/p79/6S0p/S8/S86v7u+b+X3Evye78kfSl9er3u1PO+p73U93r2X19Pf0n573rP0/f0vXv6979LXuqf++f/Xv3f/9
mne5f+qXv9vD0vaS8p/8m/7Ol+p77XpX/a8z9fS/pT7un+9PX8p06v9L+S/D+Sp6Te9+tVz
6mTfv+T//9IeknS//RS/09PSv8z9f9nOf3PfvqXfOq0P3V6un88PT96+p/+/z+v10u9pE5n7
/9Zz/8fT++f9PT09J6+p/S86v7p/z+v/0pPaS/JS/pL/l7y/p6Sf0rJf7LvvST9/r0kfynv
UvKSkt7/pOT/3VLe7/L2/097+pPyp//3Lml7p/+fvPR73ZLe+/fP90r96uXvUu96ek5PT+/p+XvpeUpPv56evT95Sd/Ty0vy7/9K/uXpU+/S396919P9p76v1z+n93/+ffn/tK9XPUnve+p9
vXr3f+r9e0/vqfe9pPd76v6vU/r7/p7evyf99v6X7p37p+7f//Tvf+p93Ut679/p/+p/+v/S
0zvlU6cnJXmffur7+v/0P6W9pE7/+T87/d/V0/+enqf39T73//889e6939eXekmS3uUvPUffp
6SnpGfPy9Onvpfv16uep97nKUn6X3r7vHT//L/un/T3+un+Sv+Unlf/6X/e6elV9/p69j11r
9fT997f0/v0v/d/03P0pKT09Gvv6Un3n/p++f+09/6l9/7/vP7/fUrPqXvKe1Xv37u/9/+v
9+r57+fV+z3v39/Xe/p9er/39/Tpf/vX87Vf90/P9G909O85/Xun9BydpPzOnpI8p9P/vffvS
flPe/qeXmPv6evpefqep6/3/tXTe/p6eo/09H9Pr9fT8/Q8Pa/S89S9p3//pOfpOer/v089p
+6pU6cePT3pOXp6evf0vI6efh0v/fX19K7v/73ev6d3+vR0p3d6ev/7unv6eXkvPa/u9fOefl
7f607P6079XtfTe/p6evR8Xve6k56X073/vV/39P739P7Puvfv+Xv19PT++v+ev7/+f/mX3r2n
Z09P3vt6ef/v6Xl6T696T+/pPXpPr3p6T+/R8/S86unX9fR+ff88PUff3+ue3v/+P19P3v/6n6
8r7X/3w9PU/Pe3rVe3q+np6n5+l5enqeeqeevaeX/vo89X73nv5zSnr9u/7/e93f+7/pPXr17n1PvUfv09Pr9fSfXpL+XvU+PUfvUe/Re/QePU9Pz/uep/899R69S8+p9+j7ep6evr7+6/vXv+fpP3t6/1vS8/TvPyVpL/f376f7f+6f3q//v57T/3/P6f6X/z+nnv/S8z/X8/r/S0+v3qf7n+Sp7+v/+v9SUn673v9Tf5/Wp/unXv+p76f7f/+Xp6f//+6V/u969r7/X1//P6dPr/uUv3v/u31/+t//u3f9z6n/v+p/79L3/v/6v3t6p/rXvU9576n7f8/+U7r/9H57ev8zPf3/S++U/rve/6vX67/UveT9L/27l6T89P5vS//vUpKS+9/X67/+3//+X6/U8/SvT/enU97rSv/7Sf/7n33v17ue9O9779fT+/S83p+39/97SfqevnfKnvd6n5Kekvf/Py+pU/rUqVP//vXv/9fT/0/pe/p/v6efpOfpqXufltL39LpT939v/3//+r+v/P+efu8v70n/U096f/+f/pfe7/un9/Xq6X/q6Y879f9v3U9PSfIvvST9u16Sp6SnpH/Op56e7un/6f3vS3peev/pS/6nf8n/5eXpeXmX/u9/+X/S856+nvQ/e+8v7+/S//SSf95T/9fX9p/0X/9L93T/7//v6Uu9Sv/5X97f/0/5v/xL+p7+L++U3v/8L/9L30v3T09KX9f/+770T/f6n/r/fS/9O/f+f/rT+9PT8/R8SfpK/p+S/8mXpC89p16vnv97el57yUvPf+q0pOfov6yXvXv/0tPz7Nl7SnnP/T/vS+9PT/7v6f/yp+fV/9OT96dnyb98Sf7vXvIuOfUvKbnvI/+3l7rXy7uU/Evv99L79f/nJfnUv/+9Xur7dD/pf/p79/6S0p/S8/S86v7u+b+X3Evye78kfSl9er3u1PO+p73U93r2X19Pf0n573rP0/f0vXv6979LXuqf++f/Xv3f/9
"""

def inicializar():
    if not os.path.exists(ARQ_HIST):
        pd.DataFrame(columns=["Data", "Ação", "Veículo", "Usuário", "KM", "CNH", "Av_Saida", "Av_Chegada", "Av_Totais", "Obs", "Foto_Base64"]).to_csv(ARQ_HIST, index=False)
    if not os.path.exists(ARQ_MOT):
        pd.DataFrame(columns=["Nome", "Validade_CNH", "Status"]).to_csv(ARQ_MOT, index=False)
    if not os.path.exists(ARQ_VEIC):
        pd.DataFrame(columns=["Veículo", "Placa", "Ult_Revisao_KM", "Ult_Revisao_Data", "Intervalo_KM", "Status"]).to_csv(ARQ_VEIC, index=False)
    if not os.path.exists(ARQ_PECAS):
        pecas_p = ["1. Capô", "2. Parabrisa", "3. Parachoque Dianteiro", "4. Parachoque Traseiro", "5. Pneus", "6. Teto", "7. Portas Dir", "8. Portas Esq"]
        pd.DataFrame({"Item": pecas_p, "Status": ["Ativo"] * len(pecas_p)}).to_csv(ARQ_PECAS, index=False)

inicializar()

# --- FUNÇÕES CORE ---
def carregar(arq): return pd.read_csv(arq).fillna("")
def salvar(df, arq): df.to_csv(arq, index=False)

def get_status_veiculo(v_alvo):
    df_h = carregar(ARQ_HIST)
    if not df_h.empty:
        df_v = df_h[df_h['Veículo'] == v_alvo]
        if not df_v.empty:
            ult = df_v.iloc[-1]
            return {"acao": ult['Ação'], "user": ult['Usuário'], "km": int(ult['KM']), "av": str(ult['Av_Totais']) if str(ult['Av_Totais']).strip() != "" else "Nenhuma"}
    df_c = carregar(ARQ_VEIC)
    v_info = df_c[df_c['Veículo'] + " (" + df_c['Placa'] + ")" == v_alvo]
    km_ini = int(v_info.iloc[0]['Ult_Revisao_KM']) if not v_info.empty else 0
    return {"acao": "CHEGADA", "user": "Ninguém", "km": km_ini, "av": "Nenhuma"}

def converter_multiplas_fotos(uploaded_files):
    lista_b64 = []
    if uploaded_files:
        for file in uploaded_files:
            img = Image.open(file)
            img.thumbnail((800, 800))
            buf = BytesIO()
            img.save(buf, format="JPEG", quality=70)
            lista_b64.append(base64.b64encode(buf.getvalue()).decode())
    return ";".join(lista_b64)

if 'edit_v_idx' not in st.session_state: st.session_state.edit_v_idx = -1
if 'edit_m_idx' not in st.session_state: st.session_state.edit_m_idx = -1
if 'edit_p_idx' not in st.session_state: st.session_state.edit_p_idx = -1

# --- EXIBIÇÃO DO LOGOTIPO EM TODAS AS ABAS ---
st.image(base64.b64decode(LOGO_DIV), width=300)
st.title("Gestão de Fro") # Título simplificado conforme pedido

tabs = st.tabs(["⚙️ Gestão & Cadastro", "📤 Saída", "📥 Chegada", "🔧 Manutenção", "📋 Histórico"])

# --- ABA 1: GESTÃO ---
with tabs[0]:
    c1, c2, c3 = st.columns(3)
    df_h = carregar(ARQ_HIST)
    with c1:
        st.subheader("🚗 Veículos")
        df_v = carregar(ARQ_VEIC)
        with st.expander("➕ Novo/Editar", expanded=(st.session_state.edit_v_idx != -1)):
            v_idx = st.session_state.edit_v_idx
            with st.form("f_v"):
                v_m = df_v.iloc[v_idx]['Veículo'] if v_idx != -1 else ""
                v_p = df_v.iloc[v_idx]['Placa'] if v_idx != -1 else ""
                v_k = int(df_v.iloc[v_idx]['Ult_Revisao_KM']) if v_idx != -1 else 0
                v_d_val = datetime.strptime(str(df_v.iloc[v_idx]['Ult_Revisao_Data']), '%Y-%m-%d').date() if v_idx != -1 else None
                v_mod = st.text_input("Modelo", value=v_m)
                v_pla = st.text_input("Placa", value=v_p).upper().strip()
                v_km_r = st.number_input("KM Última Revisão", value=v_k)
                v_dt_r = st.date_input("Data Última Revisão", value=v_d_val, format="DD/MM/YYYY")
                if st.form_submit_button("Salvar"):
                    if v_mod and v_pla and v_dt_r:
                        nova = {"Veículo": v_mod, "Placa": v_pla, "Ult_Revisao_KM": v_km_r, "Ult_Revisao_Data": v_dt_r, "Intervalo_KM": 10000, "Status": "Ativo"}
                        if v_idx == -1: df_v = pd.concat([df_v, pd.DataFrame([nova])], ignore_index=True)
                        else: 
                            for k, v in nova.items(): df_v.at[v_idx, k] = v
                        salvar(df_v, ARQ_VEIC); st.session_state.edit_v_idx = -1; st.rerun()
        for i, r in df_v.iterrows():
            with st.container(border=True):
                st.write(f"**{r['Veículo']} ({r['Placa']})**")
                col_b1, col_b2 = st.columns(2)
                if col_b1.button("📝", key=f"ev{i}"): st.session_state.edit_v_idx = i; st.rerun()
                if col_b2.button("🚫", key=f"bv{i}"):
                    df_v.at[i, 'Status'] = "Inativo" if r['Status'] == "Ativo" else "Ativo"
                    salvar(df_v, ARQ_VEIC); st.rerun()

    with c2:
        st.subheader("👤 Motoristas")
        df_m = carregar(ARQ_MOT)
        with st.expander("➕ Novo/Editar", expanded=(st.session_state.edit_m_idx != -1)):
            m_idx = st.session_state.edit_m_idx
            with st.form("f_m"):
                m_n = df_m.iloc[m_idx]['Nome'] if m_idx != -1 else ""
                m_v_val = datetime.strptime(str(df_m.iloc[m_idx]['Validade_CNH']), '%Y-%m-%d').date() if m_idx != -1 else None
                m_nome = st.text_input("Nome", value=m_n)
                m_cnh = st.date_input("Validade CNH", value=m_v_val, format="DD/MM/YYYY")
                if st.form_submit_button("Salvar"):
                    if m_nome and m_cnh:
                        nova = {"Nome": m_nome, "Validade_CNH": m_cnh, "Status": "Ativo"}
                        if m_idx == -1: df_m = pd.concat([df_m, pd.DataFrame([nova])], ignore_index=True)
                        else:
                            for k, v in nova.items(): df_m.at[m_idx, k] = v
                        salvar(df_m, ARQ_MOT); st.session_state.edit_m_idx = -1; st.rerun()
        for i, r in df_m.iterrows():
            with st.container(border=True):
                st.write(f"**{r['Nome']}**")
                cm1, cm2 = st.columns(2)
                if cm1.button("📝", key=f"em{i}"): st.session_state.edit_m_idx = i; st.rerun()
                if cm2.button("🚫", key=f"bm{i}"):
                    df_m.at[i, 'Status'] = "Inativo" if r['Status'] == "Ativo" else "Ativo"
                    salvar(df_m, ARQ_MOT); st.rerun()

    with c3:
        st.subheader("📋 Checklist")
        df_p = carregar(ARQ_PECAS)
        with st.expander("➕ Novo/Editar Item", expanded=(st.session_state.edit_p_idx != -1)):
            p_idx = st.session_state.edit_p_idx
            with st.form("f_p"):
                p_v = df_p.iloc[p_idx]['Item'] if p_idx != -1 else ""
                n_p_desc = st.text_input("Descrição", value=p_v)
                if st.form_submit_button("Salvar"):
                    if n_p_desc:
                        if p_idx == -1: df_p = pd.concat([df_p, pd.DataFrame([{"Item": n_p_desc, "Status": "Ativo"}])], ignore_index=True)
                        else: df_p.at[p_idx, "Item"] = n_p_desc
                        salvar(df_p, ARQ_PECAS); st.session_state.edit_p_idx = -1; st.rerun()
        for i, r in df_p.iterrows():
            with st.container(border=True):
                st.write(f"**{r['Item']}**")
                cp1, cp2 = st.columns(2)
                if cp1.button("📝", key=f"ep{i}"): st.session_state.edit_p_idx = i; st.rerun()
                if cp2.button("🚫", key=f"bp{i}"):
                    df_p.at[i, 'Status'] = "Inativo" if r['Status'] == "Ativo" else "Ativo"
                    salvar(df_p, ARQ_PECAS); st.rerun()

# --- ABA 2: SAÍDA ---
with tabs[1]:
    st.header("📤 Registrar Saída")
    df_v_at = carregar(ARQ_VEIC)[carregar(ARQ_VEIC)['Status'] == "Ativo"]
    df_m_at = carregar(ARQ_MOT)[carregar(ARQ_MOT)['Status'] == "Ativo"]
    p_lista = carregar(ARQ_PECAS)[carregar(ARQ_PECAS)['Status'] == "Ativo"]['Item'].tolist()
    v_s = st.selectbox("Veículo", ["Selecione..."] + [f"{r['Veículo']} ({r['Placa']})" for _, r in df_v_at.iterrows()])
    m_s = st.selectbox("Motorista", ["Selecione..."] + df_m_at['Nome'].tolist())
    if v_s != "Selecione..." and m_s != "Selecione...":
        st_v = get_status_veiculo(v_s)
        if st_v["acao"] == "SAÍDA": st.error(f"Bloqueado: Com {st_v['user']}")
        else:
            km_sai = st.number_input("KM Inicial", value=st_v['km'], min_value=st_v['km'])
            fotos_s = st.file_uploader("Fotos", accept_multiple_files=True)
            av_bruto = st_v['av'].replace(' | ', ',').replace('|', ',')
            d_av = [x.strip() for x in av_bruto.split(',')] if st_v['av'] != "Nenhuma" else []
            checklist = st.multiselect("Avarias Atuais", list(set(p_lista + d_av)), default=d_av)
            if st.button("🚀 Confirmar"):
                nova = pd.DataFrame([{"Data": get_data_hora_br(), "Ação": "SAÍDA", "Veículo": v_s, "Usuário": m_s, "KM": km_sai, "Av_Saida": ", ".join(checklist), "Av_Chegada": "Pendente", "Av_Totais": ", ".join(checklist), "Foto_Base64": converter_multiplas_fotos(fotos_s)}])
                salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST); st.rerun()

# --- ABAS 3 E 4 (SIMPLIFICADAS) ---
with tabs[2]:
    st.header("📥 Registrar Chegada")
    veiculos_uso = [v for v in [f"{r['Veículo']} ({r['Placa']})" for _, r in carregar(ARQ_VEIC).iterrows()] if get_status_veiculo(v)["acao"] == "SAÍDA"]
    v_ret = st.selectbox("Veículo", ["Selecione..."] + veiculos_uso)
    if v_ret != "Selecione...":
        st_ret = get_status_veiculo(v_ret)
        km_f = st.number_input("KM Final", min_value=st_ret['km'], value=st_ret['km'])
        fotos_c = st.file_uploader("Fotos Chegada", accept_multiple_files=True)
        if st.button("🏁 Confirmar Chegada"):
            nova = pd.DataFrame([{"Data": get_data_hora_br(), "Ação": "CHEGADA", "Veículo": v_ret, "Usuário": st_ret['user'], "KM": km_f, "Av_Saida": st_ret['av'], "Av_Totais": st_ret['av'], "Foto_Base64": converter_multiplas_fotos(fotos_c)}])
            salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST); st.rerun()

with tabs[3]:
    st.header("🔧 Reparos")
    v_m = st.selectbox("Veículo oficina", ["Selecione..."] + [f"{r['Veículo']} ({r['Placa']})" for _, r in carregar(ARQ_VEIC).iterrows()])
    if v_m != "Selecione...":
        st_man = get_status_veiculo(v_m)
        av_limpo = st_man['av'].replace(' | ', ',').replace('|', ',')
        lista_atuais = [x.strip() for x in av_limpo.split(',')] if st_man['av'] != "Nenhuma" else []
        reparados = st.multiselect("Consertados:", lista_atuais)
        if st.button("🛠️ Salvar Reparo"):
            restantes = [i for i in lista_atuais if i not in reparados]
            nova = pd.DataFrame([{"Data": get_data_hora_br(), "Ação": "REPARO", "Veículo": v_m, "Usuário": "Oficina", "KM": st_man['km'], "Av_Totais": " | ".join(restantes) if restantes else "Nenhuma"}])
            salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST); st.rerun()

# --- HISTÓRICO ---
with tabs[4]:
    st.header("📋 Histórico")
    df_h = carregar(ARQ_HIST)
    if not df_h.empty:
        idx = st.selectbox("ID:", df_h.index)
        st.dataframe(df_h.drop(columns=["Foto_Base64"]), use_container_width=True)
        fb64 = df_h.iloc[idx]["Foto_Base64"]
        if fb64:
            for f in fb64.split(";"): st.image(base64.b64decode(f), width=400)
