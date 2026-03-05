// Lottie Creator AEP Parser - Extracted & Beautified Code
// Source: https://creator.lottiefiles.com/assets/vendor-o6fNbpjT.js (bytes 1860200-1950800)
// and: https://creator.lottiefiles.com/assets/index-ClcjWm6I.js (bytes 579000-595000)

// ====== VENDOR BUNDLE: Core AEP Parser ======

// [FIX] Reconstructed missing head: Object.defineProperty helper and class field decorator
var __defProp = Object.defineProperty;
var bn = (eA, AA, tA) => AA in eA ? __defProp(eA, AA, {
  enumerable:!0,configurable:!0,writable:!0,value:tA
}):eA[AA]=tA,l$4=(eA,AA,tA)=>(bn(eA,typeof AA!="symbol"?AA+"":AA,tA),tA),he$3=class{
  constructor(AA=0,tA=""){
    l$4(this,"id"),l$4(this,"name"),this.id=AA,this.name=tA
  }
},_e$3=class extends he$3{
  constructor(){
    super(...arguments),l$4(this,"items",[])
  }
},Oe$2=class{
  constructor(){
    l$4(this,"assets",new Map),l$4(this,"compositions",[]),l$4(this,"currentItem"),l$4(this,"effects",new Map),l$4(this,"folder",new _e$3(-1))
  }
},q$3=class extends he$3{
  constructor(){
    super(...arguments),l$4(this,"color",new I$4),l$4(this,"duration",0),l$4(this,"framerate",0),l$4(this,"height",0),l$4(this,"inTime",0),l$4(this,"layers",[]),l$4(this,"markers"),l$4(this,"outTime",0),l$4(this,"playheadTime",0),l$4(this,"views",[]),l$4(this,"width",0)
  }scale(AA,tA){
    this.inTime*=AA,this.outTime*=AA,this.playheadTime*=AA,this.duration*=AA,this.layers.forEach(iA=>this._scaleLayers(iA,AA,tA))
  }_scaleLayers(AA,tA,iA){
    if(AA instanceof ve$3){
      if(AA.inTime*=tA,AA.outTime*=tA,AA.startTime*=tA,AA.properties.properties.forEach(rA=>{
        (rA.value instanceof R$2||rA.value instanceof O$3)&&this._scaleLayers(rA.value,tA,iA)
      }),AA.assetId){
        let rA=iA.get(AA.assetId);
        rA instanceof q$3&&rA.scale(tA,iA)
      }return
    }if(AA instanceof R$2||AA instanceof ne$3){
      (AA instanceof ne$3?AA.properties.properties:AA.properties).forEach(rA=>{
        (rA.value instanceof R$2||rA.value instanceof O$3||rA.value instanceof ne$3)&&this._scaleLayers(rA.value,tA,iA)
      });
      return
    }AA instanceof O$3&&AA.keyframes.forEach(rA=>rA.time*=tA)
  }
},W$3=class extends he$3{
  constructor(AA,tA,iA,rA,gA,nA){
    super(AA,tA),l$4(this,"fullPath"),l$4(this,"height"),l$4(this,"sequenceInfo"),l$4(this,"width"),this.fullPath=iA,this.width=rA,this.height=gA,this.sequenceInfo=nA
  }
},ye$4=class extends he$3{
  constructor(AA,tA,iA,rA,gA){
    super(AA,tA),l$4(this,"color"),l$4(this,"height"),l$4(this,"width"),this.color=iA,this.width=rA,this.height=gA
  }
},re$2=class{
  constructor(){
    l$4(this,"key","")
  }
},Ve$3=class{
  constructor(AA,tA){
    l$4(this,"matchName"),l$4(this,"value"),this.matchName=AA,this.value=tA
  }
},R$2=class extends re$2{
  constructor(){
    super(...arguments),l$4(this,"name",""),l$4(this,"properties",[]),l$4(this,"splitPosition",!1),l$4(this,"visible",!0)
  }property(AA){
    var tA;
    return(tA=this.properties.find(iA=>iA.matchName===AA))==null?void 0:tA.value
  }
},Vt$1=(eA=>(eA[eA.Linear=1]="Linear",eA[eA.Bezier=2]="Bezier",eA[eA.Hold=3]="Hold",eA))(Vt$1||{
  
}),vt$1=(eA=>(eA[eA.Normal=0]="Normal",eA[eA.Continuous=1]="Continuous",eA[eA.Auto=2]="Auto",eA))(vt$1||{
  
}),Ne$2=class{
  constructor(){
    l$4(this,"bezierMode",0),l$4(this,"inInfluence",[]),l$4(this,"inSpeed",[]),l$4(this,"inTangent",new h$7),l$4(this,"labelColor",0),l$4(this,"outInfluence",[]),l$4(this,"outSpeed",[]),l$4(this,"outTangent",new h$7),l$4(this,"roving",!1),l$4(this,"time",0),l$4(this,"transitionType",1),l$4(this,"value")
  }
},O$3=class extends re$2{
  constructor(){
    super(...arguments),l$4(this,"animated",!1),l$4(this,"components",0),l$4(this,"expression"),l$4(this,"keyframes",[]),l$4(this,"split",!1),l$4(this,"type",3),l$4(this,"value")
  }
},ve$3=class{
  constructor(){
    l$4(this,"assetId",0),l$4(this,"autoOrient",!1),l$4(this,"bicubicSampling",!1),l$4(this,"blendMode",Do$1.NORMAL),l$4(this,"continuouslyRasterize",!1),l$4(this,"effectsEnabled",!1),l$4(this,"id",0),l$4(this,"inTime",0),l$4(this,"isAdjustment",!1),l$4(this,"isGuide",!1),l$4(this,"isNull",!1),l$4(this,"labelColor",0),l$4(this,"locked",!1),l$4(this,"matteId",0),l$4(this,"matteMode",Ii.NO_TRACK_MATTE),l$4(this,"motionBlurEnabled",!1),l$4(this,"name",""),l$4(this,"outTime",0),l$4(this,"parentId",0),l$4(this,"properties",new R$2),l$4(this,"quality",1),l$4(this,"shy",!1),l$4(this,"solo",!1),l$4(this,"startTime",0),l$4(this,"threedimensional",!1),l$4(this,"timeStretch",1),l$4(this,"type",4),l$4(this,"visible",!0)
  }
},Ee$3=class{
  constructor(){
    l$4(this,"closed",!1),l$4(this,"groupInfo",{
      maxVertexCount:0,bezierCount:0
    }),l$4(this,"maximum",new h$7(0,0)),l$4(this,"minimum",new h$7(0,0)),l$4(this,"points",[])
  }
},K$3=class{
  constructor(AA,tA,iA){
    l$4(this,"midPoint"),l$4(this,"offset"),l$4(this,"value"),this.offset=AA,this.midPoint=tA,this.value=iA
  }
},ke$3=class{
  constructor(){
    l$4(this,"alphaStops",[]),l$4(this,"colorStops",[])
  }
},Fe$2=class{
  constructor(){
    l$4(this,"duration",0),l$4(this,"isProtected",!1),l$4(this,"labelColor",0),l$4(this,"name","")
  }
},ge$2=class{
  constructor(){
    l$4(this,"characterStyles",[]),l$4(this,"lineStyles",[]),l$4(this,"paragraphStyles",[]),l$4(this,"text","")
  }
},Ue$1=class{
  constructor(AA){
    l$4(this,"family"),this.family=AA
  }
},Vn=(eA=>(eA[eA.Normal=0]="Normal",eA[eA.SmallCaps=1]="SmallCaps",eA[eA.AllCaps=2]="AllCaps",eA))(Vn||{
  
}),vn$1=(eA=>(eA[eA.Normal=0]="Normal",eA[eA.Superscript=1]="Superscript",eA[eA.Subscript=2]="Subscript",eA))(vn$1||{
  
}),Ge$3=class{
  constructor(){
    l$4(this,"characterCount",0),l$4(this,"textJustify",Ks.LEFT)
  }
},ze$1=class{
  constructor(){
    l$4(this,"wrapPosition",new h$7),l$4(this,"wrapSize",new k$7)
  }
},qe$2=class{
  constructor(){
    l$4(this,"characterCount",0),l$4(this,"fauxBold",!1),l$4(this,"fauxItalic",!1),l$4(this,"fillColor",new I$4),l$4(this,"fillEnabled",!0),l$4(this,"fontIndex",0),l$4(this,"leading",0),l$4(this,"leadingAuto",!1),l$4(this,"size",0),l$4(this,"strokeColor",new I$4),l$4(this,"strokeEnabled",!1),l$4(this,"strokeOverFill",!1),l$4(this,"strokeWidth",0),l$4(this,"textTransform",0),l$4(this,"tracking",0),l$4(this,"verticalAlign",0)
  }
},Ae$2=class extends re$2{
  constructor(){
    super(...arguments),l$4(this,"documents",new O$3),l$4(this,"fonts",[])
  }
},je$3=class{
  constructor(){
    l$4(this,"defaultValue"),l$4(this,"lastValue"),l$4(this,"matchName",""),l$4(this,"name",""),l$4(this,"type",15)
  }
},He$2=class{
  constructor(){
    l$4(this,"matchName",""),l$4(this,"name",""),l$4(this,"parameterMap",new Map),l$4(this,"parameters",[])
  }
},xe$2=class extends re$2{
  constructor(){
    super(...arguments),l$4(this,"name",""),l$4(this,"parameters",new R$2)
  }
},se$2=class{
  constructor(){
    l$4(this,"layerId",0),l$4(this,"layerSource",0)
  }
},ne$3=class extends re$2{
  constructor(){
    super(...arguments),l$4(this,"index",0),l$4(this,"inverted",!1),l$4(this,"locked",!1),l$4(this,"mode",Fo$1.Add),l$4(this,"properties",new R$2)
  }
},L$4=class{
  constructor(AA,tA=null){
    this.type=AA,this.value=tA
  }
},$e$3=class{
  constructor(AA){
    l$4(this,"_lookahead",new L$4(10,null)),l$4(this,"_data"),l$4(this,"_offset",0),this._data=AA
  }_lex(){
    this._lookahead=this._lexToken()
  }_lexToken(){
    let AA;
    for(;
    ;
    ){
      if(AA=this._getChar(),AA==="")return new L$4(10);
      if(AA==="%")this._lexComment();
      else if(!/\s/.exec(AA))break
    }if(AA==="<"){
      if(AA=this._getChar(),AA==="<")return new L$4(5);
      if(AA==="")this.throwLex("<");
      else{
        if(/[0-9a-f]/i.exec(AA))return this._lexHexString(AA);
        this.throwLex(`<${
          AA
        }`)
      }
    }if(AA===">"){
      let tA=this._getChar();
      return tA!==">"&&this.throwLex(typeof tA=="string"?AA+tA:"",">>"),new L$4(6)
    }if(AA==="[")return new L$4(7);
    if(AA==="]")return new L$4(8);
    if(AA==="/")return this._lexIdentifier();
    if(AA==="(")return this._lexString();
    if(/[a-z]/i.exec(AA))return this._lexKeyword(AA);
    if(/[-+.0-9]/.exec(AA))return this._lexNumber(AA);
    this.throwLex(AA)
  }throwLex(AA,tA=void 0){
    let iA=`Unknown COS token ${
      AA
    }`;
    throw tA!==void 0&&(iA+=`, expected ${
      tA
    }`),new Error(iA)
  }_getByte(){
    if(this._offset>=this._data.length)return-1;
    let AA=this._data[this._offset];
    return this._offset+=1,AA
  }_getChar(){
    let AA=this._getByte();
    return AA===-1?"":String.fromCharCode(AA)
  }_unget(){
    if(this._offset-=1,this._offset<0)throw new Error("Buffer underflow")
  }_lexComment(){
    for(;
    ;
    ){
      let AA=this._getChar();
      if(AA===""||AA===`
`)break
    }
  }_lexNumber(AA){
    return AA==="."?this._lexNumberFract(this._getChar(),AA):AA==="+"||AA==="-"?this._lexNumberInt(this._getChar(),AA):this._lexNumberInt(AA,"")
  }_lexNumberInt(AA,tA){
    for(;
    ;
    ){
      if(AA===".")return this._lexNumberFract(this._getChar(),tA+AA);
      if(AA==="")break;
      if(/[0-9]/.exec(AA))tA+=AA,AA=this._getChar();
      else{
        this._unget();
        break
      }
    }return new L$4(1,Number(tA))
  }_lexNumberFract(AA,tA){
    for(;
    AA!=="";
    )if(/[0-9]/.exec(AA))tA+=AA,AA=this._getChar();
    else{
      this._unget();
      break
    }return new L$4(1,Number(tA))
  }_lexKeyword(AA){
    let tA=AA;
    for(;
    ;
    ){
      let iA=this._getChar();
      if(iA==="")break;
      if(/[a-z]/i.exec(iA))tA+=iA;
      else{
        this._unget();
        break
      }
    }switch(tA){
      case"true":return new L$4(4,!0);
      case"false":return new L$4(4,!1);
      case"null":return new L$4(9,null);
      default:throw new Error(`Unknown keyword ${
        tA
      }`)
    }
  }_lexString(){
    let AA="utf-8",tA=[],iA=!1;
    for(;
    ;
    ){
      let rA=this._lexStringChar();
      if(rA===-1)break;
      tA.push(rA),!iA&&tA.length===2&&(tA[0]===254&&tA[1]===255?(AA="utf-16be",tA=[]):tA[0]===255&&tA[1]===254&&(AA="utf-16le",tA=[]),iA=!0)
    }return new L$4(2,new TextDecoder(AA).decode(new Uint8Array(tA)))
  }_lexStringChar(){
    let AA=this._getByte();
    if(AA===-1)throw new Error("Unterminated String");
    let tA=String.fromCharCode(AA);
    return tA===")"?-1:tA==="\\"?this._lexStringEscape():tA==="\r"?(this._getChar()!==`
`&&this._unget(),10):tA===`
`?(this._getChar()!=="\r"&&this._unget(),10):AA}_lexStringEscape(){let AA=this._getChar();if(AA==="")throw new Error("Unterminated string");switch(AA){case"b":return 8;case"n":return 10;case"f":return 12;case"r":return 13;case"(":case")":case"\\":return AA.charCodeAt(0)}if(/[0-7]/.exec(AA)){let tA=AA;for(let iA=0;iA<2&&(AA=this._getChar(),AA!=="");iA+=1){if(!/[0-7]/.exec(AA)){this._unget();break}tA+=AA}return parseInt(tA,8)}throw new Error("Invalid escape sequence")}_lexHexString(AA){let tA=0,iA=[];for(;;){let rA=this._getChar();if(rA==="")throw new Error("Unterminated hex string");if(/[0-9a-f]/i.exec(rA))tA+=1,tA%2?iA.push(parseInt(AA+rA,16)):AA=rA;else if(rA===">"){tA%2===0&&iA.push(parseInt(`${AA}0`,16));break}else if(!/\s/.exec(rA))throw new Error(`Invalid character in hex string: ${rA}`)}return new L$4(3,new Uint8Array(iA))}_lexIdentifier(){let AA="",tA="()[]<>/%";for(;;){let iA=this._getByte();if(iA===-1)break;if(iA<33||iA>126){this._unget();break}let rA=String.fromCharCode(iA);if(rA==="#"){let gA="";for(let nA=0;nA<2;nA+=1){if(rA=this._getChar(),rA===""||!/[0-9a-f]/i.exec(rA))throw new Error("Invalid Identifier");gA+=rA}AA+=String.fromCharCode(parseInt(gA,16))}else if(tA.includes(rA)){this._unget();break}else AA+=rA}return new L$4(0,AA)}parse(){if(this._lex(),this._lookahead.type===0)return this._parseObjectContent();let AA=this._parseValue();return this._lookahead.type===10?AA:[AA].concat(this._parseArrayContent())}_parseObjectContent(){let AA=new Map;for(;!(this._lookahead.type===10||this._lookahead.type===6);){this._expect(0);let tA=this._lookahead.value;this._lex();let iA=this._parseValue();AA.set(tA,iA)}return AA}_expect(AA){if(this._lookahead.type!==AA)throw new Error(`Expected token ${AA}, got ${this._lookahead.type}`)}_parseArrayContent(){let AA=[];for(;!(this._lookahead.type===10||this._lookahead.type===8);)AA.push(this._parseValue());return AA}_parseValue(){let AA;switch(this._lookahead.type){case 2:case 3:case 9:case 4:case 0:case 1:return AA=this._lookahead.value,this._lex(),AA;case 5:return this._lex(),AA=this._parseObjectContent(),this._expect(6),this._lex(),AA;case 7:return this._lex(),AA=this._parseArrayContent(),this._expect(8),this._lex(),AA;default:throw new Error(`Expected token COS value, got ${this._lookahead.type}`)}}},Xe$2=class{decodeInt2Comp(AA){let tA=this.decodeUInt(AA),iA=1<<AA.byteLength*8-1;return tA&iA?tA-(iA<<1):tA}},ie$2=class extends Xe$2{static bufferToUint(AA){let tA=0;for(let iA of AA)tA<<=8,tA|=iA;return tA}decodeFloat32(AA){return AA.getFloat32(0,!1)}decodeFloat64(AA){return AA.getFloat64(0,!1)}decodeUInt(AA){return ie$2.bufferToUint(new Uint8Array(AA.buffer,AA.byteOffset,AA.byteLength))}},it$1=class extends Xe$2{decodeFloat32(AA){return AA.getFloat32(0,!0)}decodeFloat64(AA){return AA.getFloat64(0,!0)}decodeUInt(AA){return ie$2.bufferToUint(AA.slice().reverse())}},oe$2=class{constructor(AA){l$4(this,"type"),l$4(this,"children",[]),this.type=AA}findOptional(AA){for(let tA of this.children)if(tA.name===AA)return tA}find(AA){let tA=this.findOptional(AA);if(tA===void 0)throw Error(`${AA} not found`);return tA}findMultiple(AA){let tA=AA.map(()=>{}),iA=0;for(let rA of this.children){let gA=AA.indexOf(rA.name);if(gA!==-1&&tA[gA]===void 0&&(tA[gA]=rA,iA+=1,iA>=AA.length))break}return tA}findAll(AA){let tA=[];for(let iA of this.children)iA.name===AA&&tA.push(iA);return tA}},Q$3=class{constructor(AA,tA,iA){l$4(this,"header"),l$4(this,"length"),l$4(this,"data"),this.header=AA,this.length=tA,this.data=iA}get name(){return this.header==="LIST"?this.data.type:this.header}get list(){if(this.data instanceof oe$2)return this.data;throw Error("Not a list")}},ot$1=class{constructor(AA){this.bytes=AA}getBit(AA,tA){return(this.bytes[AA]&1<<tA)!==0}},be$3=class{constructor(AA,tA=0,iA=new ie$2){l$4(this,"buffer"),l$4(this,"offset"),l$4(this,"_endianness"),this.buffer=AA,this.offset=tA,this._endianness=iA}get endianness(){return this._endianness}readData(AA){let tA=new DataView(this.buffer,this.offset,AA);return this.offset+=AA,tA}readBytes(AA){let tA=new Uint8Array(this.buffer,this.offset,AA);return this.offset+=AA,tA}readUint(AA){return this.endianness.decodeUInt(this.readBytes(AA))}readSint(AA){return this.endianness.decodeInt2Comp(this.readBytes(AA))}readId(){return this.readString("ascii",4)}readString(AA,tA){return new TextDecoder(AA).decode(this.readBytes(tA))}readNulString(AA,tA){let iA=this.readBytes(tA),rA=iA.indexOf(0);return rA!==-1&&(iA=iA.slice(0,rA)),new TextDecoder(AA).decode(iA)}skip(AA){this.offset+=AA}readFloat32(){return this.endianness.decodeFloat32(this.readData(4))}readFloat64(){return this.endianness.decodeFloat64(this.readData(8))}readFlags(AA){return new ot$1(this.readBytes(AA))}readArray(AA,tA){let iA=[];for(let rA=0;rA<AA;rA+=1)iA.push(tA());return iA}},We$2=class extends be$3{parse(){let AA=this.readId();if(AA==="RIFF")this._endianness=new it$1;else if(AA==="RIFX")this._endianness=new ie$2;else throw new Error("Unknown format");let tA=this.readUint(4),iA=this.readId();this.onFileStart(iA);let rA=new Q$3(AA,tA,this.parseChunkList(new oe$2(iA),tA-4));return this.onFileEnd(rA),rA}onFileStart(AA){}onFileEnd(AA){}parseChunkList(AA,tA){let iA=this.offset+tA;for(;this.offset<iA;){let rA=this.parseChunk();AA.children.push(rA)}if(this.offset>iA)throw new Error("Chunk is too large");return AA}customParseChunk(AA,tA){}customParseList(AA,tA,iA){}_parseChunkData(AA,tA){if(AA==="LIST"){let rA=this.readId(),gA=this.customParseList(AA,tA,rA);return gA!==void 0?gA:new Q$3(AA,tA,this.parseChunkList(new oe$2(rA),tA-4))}let iA=this.customParseChunk(AA,tA);return iA===void 0&&(iA=this.readBytes(tA)),new Q$3(AA,tA,iA)}parseChunk(){let AA=this.readId(),tA=this.readUint(4),iA=this._parseChunkData(AA,tA);return tA%2===1&&(this.offset+=1),iA}},ct$1=(eA,AA)=>{if(eA.includes(".")){let[tA,iA]=eA.split("."),rA=AA[tA];if(rA instanceof Er$1)return rA.isSplit?rA.componentMap.get(iA)??null:null}return null},Pe$3=(eA,AA)=>(AA.setX(se$4(AA.x,3)),AA.setY(se$4(AA.y,3)),AA.is3D&&AA.setZ(se$4(AA.z,3)),eA.is3D&&!AA.is3D?new h$7(AA.x,AA.y,0):!eA.is3D&&AA.is3D?new h$7(AA.x,AA.y):AA),Ke$1=eA=>eA>=0&&eA<=255?eA:eA>=0&&eA<=1?eA*255:eA>255?Math.min(255,Math.max(0,eA/255)):Math.min(255,Math.max(0,eA)),lt$1=(eA,AA,tA=1e-5)=>Math.abs(eA-AA)<=tA;function Bn(eA){let AA=[];for(let tA of eA.children)tA.tagName!=="array.type"&&AA.push(Ye$1(tA));return AA}function Ye$1(eA){switch(eA.tagName){case"prop.map":return Ye$1(eA.firstElementChild);case"prop.list":return In(eA);case"array":return Bn(eA);case"int":case"float":return Number(eA.textContent);case"string":return eA.textContent;default:return}}function In(eA){let AA=new Map;for(let tA of eA.children)if(tA.tagName==="prop.pair"){let iA=tA.firstElementChild.textContent,rA=Ye$1(tA.lastElementChild);AA.set(iA,rA)}return AA}function Bt$1(eA){return Ye$1(eA.documentElement)}var Be$3=class extends We$2{customParseChunk(AA,tA){switch(AA){case"Utf8":case"alas":return this.readString("utf-8",tA);case"tdmn":return this.readNulString("utf-8",tA);case"wsnm":return this.readString("utf-16",tA);case"tdsn":case"fnam":case"pdnm":return this.parseChunkList(new oe$2(""),tA);default:return}}onFileEnd(AA){}onFileStart(AA){if(AA!=="Egg!")throw new Error("Invalid AEP file")}customParseList(AA,tA,iA){if(iA==="btdk")return new Q$3(iA,tA,this.readBytes(tA-4))}},pt$2=class{constructor(AA){this.endianness=AA,l$4(this,"_compChunks",new Map),l$4(this,"_layerPropKeyIndexMap",new Map)}_getIndexedLayerPropKey(AA){let tA=this._layerPropKeyIndexMap.get(AA);return tA===void 0?(this._layerPropKeyIndexMap.set(AA,1),AA):(this._layerPropKeyIndexMap.set(AA,tA+1),`${AA} ${tA}`)}chunkData(AA){if(!(AA.data instanceof Uint8Array))throw Error("Not a binary chunk");return new be$3(AA.data.buffer,AA.data.byteOffset,this.endianness)}parseProject(AA){let tA=new Oe$2,[iA,rA]=AA.list.findMultiple(["Fold","EfdG"]);if(rA!==void 0&&this._parseEffects(rA.list.findAll("EfDf"),tA),!iA)throw new Error("No Fold chunk found");return this._parseFolder(iA,tA.folder,tA),tA.compositions.forEach(gA=>{this._parseComposition(gA,this._compChunks.get(gA.id),tA)}),tA}_processItem(AA,tA,iA){let[rA,gA]=AA.list.findMultiple(["idta","Utf8"]);if(!rA)return;let nA=this._utf8Name(gA),oA=this.chunkData(rA),sA=oA.readUint(2);oA.skip(14);let aA=oA.readUint(4);if(sA===1){let IA=new _e$3(aA,nA);tA.items.push(IA),this._parseFolder(AA,IA,iA)}else if(sA===4){let IA=new q$3(aA,nA);iA.compositions.push(IA),iA.assets.set(aA,IA),this._compChunks.set(aA,AA.list),tA.items.push(IA)}else sA===7&&this._parseAsset(aA,AA.list.find("Pin "),tA,iA)}_parseFolder(AA,tA,iA){let rA;for(let gA=0;gA<AA.list.children.length;gA+=1){let nA=AA.list.children[gA];nA.name==="Item"?this._processItem(nA,tA,iA):nA.name==="fiac"?this.chunkData(nA).readUint(nA.length)&&(iA.currentItem=rA):nA.name==="Sfdr"&&nA.list.children.filter(oA=>oA.name==="Item"||oA.name==="Sfdr").flatMap(oA=>oA.name==="Sfdr"?oA.list.children.filter(sA=>sA.name==="Item"):oA).forEach(oA=>this._processItem(oA,tA,iA))}}_parseAsset(AA,tA,iA,rA){let[gA,nA,oA]=tA.list.findMultiple(["sspc","Als2","opti"]),sA=tA.list.findAll("Utf8");if(gA===void 0||oA===void 0)return;let aA=sA.map(yA=>this._utf8Name(yA)).join(""),IA,CA=this.chunkData(gA);CA.skip(32);let EA=CA.readUint(2);CA.skip(2);let BA=CA.readUint(2);CA.skip(2);let lA=CA.readUint(2);CA.skip(132);let QA=CA.readUint(2);CA.skip(2);let cA=CA.readUint(2);CA.skip(2);let uA=CA.readUint(2),dA=this.chunkData(oA),fA=dA.readString("utf-8",4);if(dA.skip(2),dA.skip(4),fA==="Soli"){let yA=new I$4,wA=MA=>MA===255?MA:MA*255;yA.setAlpha(dA.readFloat32()),yA.setRed(wA(dA.readFloat32())),yA.setGreen(wA(dA.readFloat32())),yA.setBlue(wA(dA.readFloat32())),IA=new ye$4(AA,dA.readNulString("utf-8",256),yA,EA,BA)}else{if(!nA)return;let yA=JSON.parse(nA.list.find("alas").data);aA===""&&(aA=yA.fullpath.replaceAll("\\","/").split("/").slice(-1)[0]),IA=new W$3(AA,aA,yA.fullpath,EA,BA,yA.target_is_folder?{count:lA,start:QA,end:cA,maxLength:uA}:void 0)}return rA.assets.set(AA,IA),iA.items.push(IA),IA}_parseComposition(AA,tA,iA){let rA=this.chunkData(tA.find("cdta"));rA.skip(4);let gA=rA.readUint(4),nA=rA.readUint(4);AA.framerate=nA/gA,rA.skip(9),AA.playheadTime=rA.readUint(2),rA.skip(2);let oA=rA.readUint(2)/AA.framerate||1;AA.playheadTime/=oA,rA.skip(2),AA.inTime=rA.readUint(2),rA.skip(2);let sA=rA.readUint(2)/AA.framerate||1;AA.inTime/=sA,rA.skip(2),AA.outTime=rA.readUint(2),rA.skip(2);let aA=rA.readUint(2)/AA.framerate||1;rA.skip(2),AA.duration=rA.readUint(2),rA.skip(2);let IA=rA.readUint(2)/AA.framerate||1;AA.duration/=IA,AA.outTime===65535?AA.outTime=AA.duration:AA.outTime/=aA,rA.skip(1);let CA=rA.readUint(1),EA=rA.readUint(1),BA=rA.readUint(1);AA.color.setRed(CA),AA.color.setGreen(EA),AA.color.setBlue(BA),rA.skip(85),AA.width=rA.readUint(2),AA.height=rA.readUint(2),rA.skip(12),tA.children.forEach(lA=>{lA.name==="Layr"?AA.layers.push(this._parseLayer(lA)):lA.name==="SecL"?AA.markers=this._parseLayer(lA):(lA.name==="CLay"||lA.name==="DLay"||lA.name==="SLay")&&AA.views.push(this._parseLayer(lA))})}_parseLayer(AA){let tA=new ve$3,[iA,rA,gA]=AA.list.findMultiple(["ldta","Utf8","tdgp"]),nA=this.chunkData(iA);tA.name=this._utf8Name(rA),tA.id=nA.readUint(4),tA.quality=nA.readUint(2),nA.skip(2);let oA=nA.readSint(4),sA=nA.readSint(4),aA=nA.readUint(4),IA=nA.readSint(4),CA=nA.readUint(4),EA=nA.readSint(4),BA=nA.readUint(4),lA=nA.readFlags(4);tA.assetId=nA.readUint(4),nA.skip(17),tA.labelColor=nA.readUint(1),nA.skip(2),nA.skip(32),tA.blendMode=nA.readUint(4),nA.skip(4),tA.matteMode=nA.readUint(4),nA.skip(2);let QA=nA.readUint(2);return nA.skip(19),tA.type=nA.readUint(1),tA.parentId=nA.readUint(4),nA.skip(24),tA.matteId=nA.readUint(4),tA.isGuide=lA.getBit(1,1),tA.bicubicSampling=lA.getBit(1,6),tA.autoOrient=lA.getBit(2,0),tA.isAdjustment=lA.getBit(2,1),tA.threedimensional=lA.getBit(2,2),tA.solo=lA.getBit(2,3),tA.isNull=lA.getBit(2,7),tA.visible=lA.getBit(3,0),tA.effectsEnabled=lA.getBit(3,2),tA.motionBlurEnabled=lA.getBit(3,3),tA.locked=lA.getBit(3,5),tA.shy=lA.getBit(3,6),tA.continuouslyRasterize=lA.getBit(3,7),tA.startTime=sA/aA,tA.outTime=EA/BA,tA.inTime=IA/CA,tA.timeStretch=oA/QA,this._parsePropertyGroup(gA.list,tA.properties,tA.id.toString()),tA}_parsePropertyGroup(AA,tA,iA){let rA="";for(let gA=0;gA<AA.children.length;gA+=1){let nA=AA.children[gA];if(nA.header==="tdmn")rA=nA.data;else if(nA.header==="tdsb"){let oA=this.chunkData(nA).readFlags(4);tA.visible=oA.getBit(3,0),tA.splitPosition=oA.getBit(3,1)}else if(nA.header==="tdsn")tA.name=this._utf8Name(nA.list.findOptional("Utf8"));else if(nA.name==="mkif"){let oA=new ne$3,sA=this.chunkData(nA);switch(oA.inverted=!!sA.readUint(1),oA.locked=!!sA.readUint(1),sA.skip(4),sA.readUint(2)){default:case 0:oA.mode=Fo$1.None;break;case 1:oA.mode=Fo$1.Add;break;case 2:oA.mode=Fo$1.Subtract;break;case 3:oA.mode=Fo$1.Intersect;break;case 4:oA.mode=Fo$1.Darken;break;case 5:oA.mode=Fo$1.Lighten;break;case 6:oA.mode=Fo$1.Difference;break}gA+=1,sA.skip(3),oA.index=sA.readUint(1),oA.properties=this._parseProperty(AA.children[gA]),tA.properties.push(new Ve$3(rA,oA)),rA=""}else if(nA.name==="OvG2"||nA.name==="blsi"||nA.name==="blsv")rA="";else if(rA!==""){let oA="";if(nA.name==="tdgp"&&rA==="ADBE Vector Group"){let IA=this._utf8Name(nA.list.find("tdsn").list.findOptional("Utf8"));oA=IA?` - ${IA}`:""}let sA=this._getIndexedLayerPropKey(iA?`${iA}/${rA}${oA}`:rA),aA=this._parseProperty(nA,sA);if(!aA)continue;aA.key=sA,tA.properties.push(new Ve$3(rA,aA)),rA=""}}}_parseProperty(AA,tA){if(AA.name==="tdgp"){let iA=new R$2;return this._parsePropertyGroup(AA.list,iA,tA),iA}else{if(AA.name==="sspc")return this._parseEffectInstance(AA.list);if(AA.name==="tdbs")return this._parseAnimatedProperty(AA.list,[]);if(AA.name==="om-s")return this._parseAnimatedShape(AA.list);if(AA.name==="GCst")return this._parseAnimatedGradient(AA.list);if(AA.name==="otst")return this._parseAnimatedOrientation(AA.list);if(AA.name==="mrst")return this._parseAnimatedMarker(AA.list);if(AA.name==="btds")return this._parseAnimatedText(AA.list)}return null}_parseAnimatedProperty(AA,tA=[]){let iA=new O$3,[rA,gA,nA,oA,sA,aA,IA,CA]=AA.findMultiple(["tdsb","tdb4","cdat","list","Utf8","tdpi","tdps","tdli"]),EA=this.chunkData(rA).readFlags(4);iA.split=EA.getBit(3,1);let BA=this.chunkData(gA);BA.skip(2),iA.components=BA.readUint(2);let lA=BA.readFlags(2).getBit(1,3);BA.skip(7);let QA=BA.readUint(4);BA.skip(39);let cA=BA.readFlags(4),uA=cA.getBit(1,0),dA=cA.getBit(3,0),fA=cA.getBit(3,2);if(BA.skip(8),lA?iA.type=2:dA?iA.type=0:uA?iA.type=1:fA?iA.type=5:iA.type=3,iA.animated=BA.readUint(1)===1,fA&&aA)iA.type=4,iA.value=new se$2,iA.value.layerId=this.chunkData(aA).readUint(4),IA&&(iA.value.layerSource=this.chunkData(IA).readSint(4));else if(fA&&CA)iA.type=6,iA.value=this.chunkData(CA).readUint(4);else if(nA!==void 0){let yA=this.chunkData(nA);iA.value=this._propertyValue(0,yA.readArray(iA.components,yA.readFloat64.bind(yA)),tA,iA.type)}if(oA!==void 0){let yA=this._listValues(oA);for(let wA=0;wA<yA.length;wA+=1)iA.keyframes.push(this._loadKeyframe(wA,yA[wA],iA,tA,QA))}return sA!==void 0&&(iA.expression=this._utf8Name(sA)),iA}_propertyValue(AA,tA,iA,rA){if(rA===1)return iA[AA];if(rA===0){let gA=tA[1],nA=tA[2],oA=tA[3],sA=tA[0],aA=Ke$1(gA),IA=Ke$1(nA),CA=Ke$1(oA),EA=Math.min(1,Math.max(0,sA));return new I$4(aA,IA,CA,EA)}else return new h$7(...tA)}_listValues(AA){let[tA,iA]=AA.list.findMultiple(["lhd3","ldat"]),rA=this.chunkData(tA);rA.skip(10);let gA=rA.readUint(2);rA.skip(6);let nA=rA.readUint(2),oA=gA*nA;if(!(iA instanceof Q$3))return[];if(iA.length<oA)throw new Error("Not enough list values");let sA=iA.data,aA=sA.byteOffset,IA=[];for(let CA=0;CA<gA;CA+=1)IA.push(new be$3(sA.buffer,aA+CA*nA,this.endianness));return IA}_processSpeedValue(AA){return Number.isNaN(AA)?0:AA}_loadKeyframe(AA,tA,iA,rA,gA){let nA=new Ne$2;tA.skip(1);let oA=tA.readSint(4);nA.time=oA/gA;let sA=tA.readUint(1);nA.transitionType=sA,nA.labelColor=tA.readUint(1);let aA=tA.readFlags(1);if(nA.roving=aA.getBit(0,5),aA.getBit(0,3)?nA.bezierMode=1:aA.getBit(0,4)?nA.bezierMode=2:nA.bezierMode=0,iA.type===1)tA.skip(16),nA.inSpeed.push(this._processSpeedValue(tA.readFloat64())),nA.inInfluence.push(tA.readFloat64()),nA.outSpeed.push(this._processSpeedValue(tA.readFloat64())),nA.outInfluence.push(tA.readFloat64()),nA.value=rA[AA];else if(iA.type===3||iA.type===5)nA.value=new h$7(...tA.readArray(iA.components,tA.readFloat64.bind(tA))),nA.inSpeed=tA.readArray(iA.components,()=>this._processSpeedValue(tA.readFloat64())),nA.inInfluence=tA.readArray(iA.components,tA.readFloat64.bind(tA)),nA.outSpeed=tA.readArray(iA.components,()=>this._processSpeedValue(tA.readFloat64())),nA.outInfluence=tA.readArray(iA.components,tA.readFloat64.bind(tA));else if(iA.type===2)tA.skip(16),nA.inSpeed.push(this._processSpeedValue(tA.readFloat64())),nA.inInfluence.push(tA.readFloat64()),nA.outSpeed.push(this._processSpeedValue(tA.readFloat64())),nA.outInfluence.push(tA.readFloat64()),nA.value=new h$7(...tA.readArray(iA.components,tA.readFloat64.bind(tA))),nA.inTangent=new h$7(...tA.readArray(iA.components,tA.readFloat64.bind(tA))),nA.outTangent=new h$7(...tA.readArray(iA.components,tA.readFloat64.bind(tA)));else if(iA.type===0){tA.skip(16),nA.inSpeed.push(this._processSpeedValue(tA.readFloat64())),nA.inInfluence.push(tA.readFloat64()),nA.outSpeed.push(this._processSpeedValue(tA.readFloat64())),nA.outInfluence.push(tA.readFloat64());let IA=tA.readArray(iA.components,tA.readFloat64.bind(tA));nA.value=new I$4(IA[1],IA[2],IA[3],IA[0]/255)}return nA}_parseAnimatedShape(AA){let[tA,iA]=AA.findMultiple(["omks","tdbs"]),rA=0,gA=tA.list.findAll("shap").map(nA=>{let oA=this._parseBezier(nA.list);return rA=Math.max(rA,oA.points.length/3),oA});return gA.forEach(nA=>{nA.groupInfo.maxVertexCount=rA,nA.groupInfo.bezierCount=gA.length}),this._parseAnimatedProperty(iA.list,gA)}_parseBezier(AA){let tA=new Ee$3,iA=this.chunkData(AA.find("shph"));iA.skip(3),tA.closed=!iA.readFlags(1).getBit(0,3),tA.minimum.setX(iA.readFloat32()),tA.minimum.setY(iA.readFloat32()),tA.maximum.setX(iA.readFloat32()),tA.maximum.setY(iA.readFloat32());for(let rA of this._listValues(AA.find("list"))){let gA=rA.readFloat32(),nA=rA.readFloat32();Number.isNaN(gA)||Number.isNaN(nA)||tA.points.push(new h$7(gA,nA))}return tA}_parseAnimatedGradient(AA){let[tA,iA]=AA.findMultiple(["GCky","tdbs"]),rA=tA.list.findAll("Utf8").map(gA=>this._parseGradient(gA.data));return this._parseAnimatedProperty(iA.list,rA)}_parseGradient(AA){let tA=new DOMParser$1().parseFromString(AA,"text/xml"),iA=Bt$1(tA).get("Gradient Color Data"),rA=new ke$3;for(let gA of iA.get("Color Stops").get("Stops List").values()){let nA=gA.get("Stops Color");rA.colorStops.push(new K$3(nA[0],nA[1],new I$4(nA[2]*255,nA[3]*255,nA[4]*255,nA[5])))}for(let gA of iA.get("Alpha Stops").get("Stops List").values()){let nA=gA.get("Stops Alpha");rA.alphaStops.push(new K$3(nA[0],nA[1],nA[2]))}return rA}_parseAnimatedOrientation(AA){let[tA,iA]=AA.findMultiple(["otky","tdbs"]),rA=tA.list.findAll("otda").map(gA=>this._parseOrientation(gA));return this._parseAnimatedProperty(iA.list,rA)}_parseOrientation(AA){let tA=this.chunkData(AA),iA=tA.readFloat64(),rA=tA.readFloat64(),gA=tA.readFloat64();return new h$7(iA,rA,gA)}_parseAnimatedMarker(AA){let[tA,iA]=AA.findMultiple(["mrky","tdbs"]),rA=tA.list.findAll("Nmrd").map(gA=>this._parseMarker(gA));return this._parseAnimatedProperty(iA.list,rA)}_parseMarker(AA){let tA=new Fe$2,iA=this.chunkData(AA.list.find("NmHd"));tA.name=this._utf8Name(AA.list.findOptional("Utf8")),iA.skip(3),tA.isProtected=iA.readFlags(1).getBit(0,1),iA.skip(4);let rA=iA.readUint(4),gA=iA.readUint(4);return tA.duration=rA/gA,tA.labelColor=iA.readUint(1),tA}_parseAnimatedText(AA){let[tA,iA]=AA.findMultiple(["btdk","tdbs"]),rA=new $e$3(tA.data).parse(),gA=new Ae$2;this._cosVal(rA,[0,1,0]).forEach(oA=>{gA.fonts.push(new Ue$1(this._cosVal(oA,[0,0,0])))});let nA=[];return this._cosVal(rA,[1,1]).forEach(oA=>{nA.push(this._parseTextDocument(oA))}),gA.documents=this._parseAnimatedProperty(iA.list,nA),gA}_parseTextDocument(AA){let tA=new ge$2;return tA.text=this._cosVal(AA,[0,0]),this._cosVal(AA,[1,2]).forEach(iA=>{!iA.has("6")||this._cosVal(iA,[6]).forEach(rA=>{if(!(rA.has("0")||rA.has("0")))return;let gA=this._cosVal(rA,[0,0]),nA=this._cosVal(rA,[1]);if((nA[2]||nA[3])&&(gA[0]||gA[1])){let oA=new ze$1;oA.wrapSize=new k$7(nA[2],nA[3]),oA.wrapPosition=new h$7(gA[0],gA[1]),tA.paragraphStyles.push(oA)}})}),this._cosVal(AA,[0,5,0]).forEach(iA=>{let rA=new Ge$3;rA.characterCount=this._cosVal(iA,[1]);let gA=this._cosVal(iA,[0,0,5]);rA.textJustify=this._cosVal(gA,0),tA.lineStyles.push(rA)}),this._cosVal(AA,[0,6,0]).forEach(iA=>{let rA=new qe$2;rA.characterCount=this._cosVal(iA,[1]);let gA=this._cosVal(iA,[0,0,6]);if(rA.fontIndex=this._cosVal(gA,0),rA.size=this._cosVal(gA,1),rA.fauxBold=this._cosVal(gA,2),rA.fauxItalic=this._cosVal(gA,3),rA.leadingAuto=this._cosVal(gA,4),rA.leading=this._cosVal(gA,5),rA.tracking=this._cosVal(gA,8),rA.textTransform=this._cosVal(gA,12),rA.verticalAlign=this._cosVal(gA,13),rA.fillEnabled=this._cosVal(gA,56)??!0,rA.fillEnabled){let nA=this._cosVal(gA,53);rA.fillColor=nA?this._cosColor(nA,[0,1]):new I$4(0,0,0)}if(rA.strokeEnabled=this._cosVal(gA,57)??!1,rA.strokeEnabled){let nA=this._cosVal(gA,54);rA.strokeColor=nA?this._cosColor(nA,[0,1]):new I$4(0,0,0),rA.strokeOverFill=this._cosVal(gA,58),rA.strokeWidth=this._cosVal(gA,63)??1}tA.characterStyles.push(rA)}),tA}_utf8Name(AA,tA=""){return AA===void 0||AA.data===pt$2._namePlaceHolder?tA:AA.data}_cosVal(AA,tA){let iA;typeof tA=="number"?iA=[tA.toString()]:iA=tA.map(gA=>gA.toString());let rA=AA;for(let gA of iA)rA=rA.get(gA);return rA}_cosColor(AA,tA){let iA=this._cosVal(AA,tA);return new I$4(iA[1]*255,iA[2]*255,iA[3]*255,iA[0])}_parseEffects(AA,tA){for(let iA of AA){let[rA,gA]=iA.list.findMultiple(["tdmn","sspc"]);if(!rA||!gA)continue;let nA=new He$2;nA.matchName=rA.data;let[oA,sA]=gA.list.findMultiple(["fnam","parT"]);oA!==void 0&&(nA.name=this._utf8Name(oA.list.findOptional("Utf8"))),tA.effects.set(nA.matchName,nA);let aA=0;for(;aA<sA.list.children.length;){let IA=sA.list.children[aA];if(IA.name!=="tdmn"){aA+=1;continue}let CA=new je$3;CA.matchName=IA.data;let EA=sA.list.children[aA+1];this._parseEffectParameter(this.chunkData(EA),CA);let BA=sA.list.children[aA+2];BA&&BA.name==="pdnm"&&!CA.name?(CA.name=this._utf8Name(BA.list.findOptional("Utf8")),aA+=3):aA+=2,nA.parameters.push(CA)}}}_parseEffectParameter(AA,tA){switch(AA.skip(14),tA.type=AA.readUint(2),tA.name=AA.readNulString("utf-8",32),AA.skip(8),tA.type){case 0:tA.lastValue=new se$2,tA.defaultValue=tA.lastValue;break;case 2:case 3:tA.lastValue=new h$7(AA.readSint(4)/65536),tA.defaultValue=new h$7(0);break;case 4:tA.lastValue=new h$7(AA.readUint(4)),tA.defaultValue=new h$7(AA.readUint(1));break;case 5:let iA=AA.readUint(1)/255,rA=AA.readUint(1),gA=AA.readUint(1),nA=AA.readUint(1);tA.lastValue=new I$4(rA,gA,nA,iA),AA.skip(1),iA=1,rA=AA.readUint(1),gA=AA.readUint(1),nA=AA.readUint(1),tA.defaultValue=new I$4(rA,gA,nA,iA);break;case 6:let oA=AA.readSint(4)/128,sA=AA.readSint(4)/128;tA.lastValue=new h$7(oA,sA),tA.defaultValue=new h$7(0,0);break;case 7:tA.lastValue=new h$7(AA.readUint(4)),AA.skip(2),tA.defaultValue=new h$7(AA.readUint(2));break;case 10:tA.lastValue=new h$7(AA.readFloat64()),tA.defaultValue=new h$7(0);break;case 18:let aA=AA.readFloat64()*512,IA=AA.readFloat64()*512,CA=AA.readFloat64()*512;tA.lastValue=new h$7(aA,IA,CA),tA.defaultValue=new h$7(0,0,0);break;default:tA.lastValue=new h$7(0),tA.defaultValue=tA.lastValue;break}return tA}_parseEffectInstance(AA){let tA=new xe$2,[iA,rA]=AA.findMultiple(["fnam","tdgp"]);return iA!==void 0&&(tA.name=this._utf8Name(iA.list.findOptional("Utf8"))),this._parsePropertyGroup(rA.list,tA.parameters),tA}},we$3=pt$2;l$4(we$3,"_namePlaceHolder","-_0_/-");var It$1={1:Do$1.NORMAL,3:Do$1.DARKEN,4:Do$1.MULTIPLY,5:Do$1.COLOR_BURN,6:Do$1.LINEAR_BURN,7:Do$1.DARKER_COLOR,9:Do$1.LIGHTEN,10:Do$1.SCREEN,11:Do$1.COLOR_DODGE,12:Do$1.LINEAR_DODGE,13:Do$1.LIGHTER_COLOR,15:Do$1.OVERLAY,16:Do$1.SOFT_LIGHT,17:Do$1.HARD_LIGHT,18:Do$1.LINEAR_LIGHT,19:Do$1.VIVID_LIGHT,20:Do$1.PIN_LIGHT,21:Do$1.HARD_MIX,23:Do$1.DIFFERENCE,24:Do$1.EXCLUSION,26:Do$1.HUE,27:Do$1.SATURATION,28:Do$1.COLOR,29:Do$1.LUMINOSITY},Lt$1={2:Do$1.NORMAL,4:Do$1.ADD,5:Do$1.MULTIPLY,6:Do$1.SCREEN,7:Do$1.OVERLAY,8:Do$1.SOFT_LIGHT,9:Do$1.HARD_LIGHT,10:Do$1.DARKEN,11:Do$1.LIGHTEN,12:Do$1.CLASSIC_DIFFERENCE,13:Do$1.HUE,14:Do$1.SATURATION,15:Do$1.COLOR,16:Do$1.LUMINOSITY,17:Do$1.STENCIL_ALPHA,18:Do$1.STENCIL_LUMA,19:Do$1.SILHOUETTE_ALPHA,20:Do$1.SILHOUETTE_LUMA,21:Do$1.LUMINESCENT_PREMUL,22:Do$1.ALPHA_ADD,24:Do$1.CLASSIC_COLOR_BURN,25:Do$1.EXCLUSION,26:Do$1.DIFFERENCE,27:Do$1.COLOR_DODGE,28:Do$1.COLOR_BURN,29:Do$1.LINEAR_DODGE,30:Do$1.LINEAR_BURN,31:Do$1.LINEAR_LIGHT,32:Do$1.VIVID_LIGHT,33:Do$1.PIN_LIGHT,34:Do$1.HARD_MIX,35:Do$1.LIGHTER_COLOR,36:Do$1.DARKER_COLOR,37:Do$1.SUBTRACT,38:Do$1.DIVIDE},ce$3=eA=>{var rA;let AA=eA.length-1,tA=AA>=0,iA;for(;tA&&(iA=eA[AA],!!iA);)iA.type==="IfStatement"?(Rt$1(iA),eA[AA]=iA,AA-=1):iA.type==="SwitchStatement"?(Mn(iA),eA[AA]=iA,tA=!1):iA.type==="ExpressionStatement"?(iA=ut$1(iA),eA[AA]=iA,tA=!1):iA.type==="TryStatement"?(ce$3(iA.block.body),((rA=iA.handler)==null?void 0:rA.body.type)==="BlockStatement"&&ce$3(iA.handler.body.body),eA[AA]=iA,tA=!1):iA.type!=="EmptyStatement"&&iA.type!=="FunctionDeclaration"&&iA.type!=="BreakStatement"||AA===0?tA=!1:AA-=1,AA<0&&(tA=!1)},ut$1=eA=>{let AA;return eA.expression.type==="Literal"||eA.expression.type==="Identifier"||eA.expression.type==="CallExpression"||eA.expression.type==="ArrayExpression"||eA.expression.type==="BinaryExpression"||eA.expression.type==="MemberExpression"||eA.expression.type==="LogicalExpression"||eA.expression.type==="UnaryExpression"||eA.expression.type==="ConditionalExpression"||eA.expression.type==="AssignmentExpression"?(AA=j$2(),AA.expression.right=eA.expression,AA):(eA.expression.type==="SequenceExpression"&&(AA=Mt$1(),AA.right=eA.expression.expressions[eA.expression.expressions.length-1],eA.expression.expressions[eA.expression.expressions.length-1]=AA),eA)},Rt$1=eA=>{var AA,tA,iA;eA.consequent.type==="BlockStatement"?ce$3(eA.consequent.body):eA.consequent.type==="ExpressionStatement"&&(eA.consequent=ut$1(eA.consequent)),((AA=eA.alternate)==null?void 0:AA.type)==="IfStatement"?Rt$1(eA.alternate):((tA=eA.alternate)==null?void 0:tA.type)==="BlockStatement"?ce$3(eA.alternate.body):((iA=eA.alternate)==null?void 0:iA.type)==="ExpressionStatement"&&(eA.alternate=ut$1(eA.alternate))},Mn=eA=>{for(let AA of eA.cases)ce$3(AA.consequent)},j$2=()=>({type:"ExpressionStatement",expression:Mt$1()}),Mt$1=()=>({right:void 0,left:{name:"$bm_rt",type:"Identifier"},type:"AssignmentExpression",operator:"="}),Ot$1=eA=>{let AA=esprimaExports.parseScript(eA,{tokens:!1,range:!0}),tA=[];Nt$1({body:AA.body,pos:0},tA),tA.sort((rA,gA)=>gA.pos-rA.pos);let iA=eA;for(let rA of tA){if(rA.undeclared.length===0)continue;let gA=`var ${rA.undeclared.join(",")};`;iA=iA.slice(0,rA.pos)+gA+iA.slice(rA.pos)}return iA},Nt$1=(eA,AA)=>{let tA=[],iA=[],rA=[];for(let gA of eA.body)gA.type==="ImportDeclaration"||gA.type==="ExportNamedDeclaration"||gA.type==="ExportDefaultDeclaration"||gA.type==="ExportAllDeclaration"||(gA.type==="ExpressionStatement"?le$3([gA.expression],iA,rA):J$3([gA],iA,rA,tA));AA.push({undeclared:rA,pos:eA.pos});for(let gA of tA)Nt$1(gA,AA)},J$3=(eA,AA,tA,iA)=>{var rA;for(let gA of eA)if(gA.type==="IfStatement")le$3([gA.test],AA,tA),J$3([gA.consequent],AA,tA,iA),gA.alternate&&J$3([gA.alternate],AA,tA,iA);else if(gA.type==="ForStatement")gA.init&&(gA.init.type==="VariableDeclaration"?J$3([gA.init],AA,tA,iA):le$3([gA.init],AA,tA)),J$3([gA.body],AA,tA,iA);else if(gA.type==="TryStatement")J$3([gA.block],AA,tA,iA),gA.handler&&J$3([gA.handler.body],AA,tA,iA);else if(gA.type==="SwitchStatement"){let nA=gA.cases.flatMap(oA=>oA.consequent);J$3(nA,AA,tA,iA)}else if(gA.type==="ExpressionStatement")le$3([gA.expression],AA,tA);else if(gA.type==="VariableDeclaration")for(let nA of gA.declarations)nA.id.type==="Identifier"&&(AA.includes(nA.id.name)||AA.push(nA.id.name));else if(gA.type==="FunctionDeclaration"){let nA=gA.params.filter(oA=>oA.type==="Identifier").map(oA=>oA.name);iA.push({body:gA.body.body,declared:[...AA,...nA],undeclared:[],pos:gA.body.range[0]+1})}else if(gA.type==="ReturnStatement"){if(((rA=gA.argument)==null?void 0:rA.type)!=="CallExpression"||!("body"in gA.argument.callee)||!("body"in gA.argument.callee.body))continue;let nA=gA.argument.callee.body.body;if(!Array.isArray(nA))continue;iA.push({body:nA,declared:AA,undeclared:[],pos:gA.argument.callee.body.range[0]+1})}else gA.type==="BlockStatement"&&J$3(gA.body,AA,tA,iA)},le$3=(eA,AA,tA)=>{for(let iA of eA)if(iA.type==="AssignmentExpression"){if(iA.left.type!=="Identifier"||iA.left.name==="value"||AA.includes(iA.left.name))continue;tA.push(iA.left.name)}else iA.type==="SequenceExpression"?le$3(iA.expressions,AA,tA):iA.type==="ConditionalExpression"?le$3([iA.test,iA.consequent,iA.alternate],AA,tA):iA.type==="LogicalExpression"&&le$3([iA.right,iA.left],AA,tA)},Nn=["position","scale","anchorPoint","rotation"],N$3=class{constructor(AA,tA){l$4(this,"body"),l$4(this,"declaredVariables"),this.body=AA,this.declaredVariables=tA}addDeclarations(AA){for(let tA of AA)tA.id.type==="Identifier"&&this.declaredVariables.push(tA.id.name)}};function Fn(eA,AA){return new N$3(eA,AA)}function Ft$1(eA,AA){let tA=[];for(let iA of eA.params)iA.type==="Identifier"&&tA.push(iA.name);return new N$3(eA.body.body,[...tA,...AA])}function Ut$1(eA,AA){return!Nn.includes(eA.name)||AA.includes(eA.name)?eA:Un(eA.name)}function Un(eA){return{type:"MemberExpression",object:{name:"$bm_transform",type:"Identifier"},property:{name:eA,type:"Identifier"},computed:!1,optional:!1}}function Gn(eA,AA,tA){let iA=eA.elements.filter(rA=>(rA==null?void 0:rA.type)!=="SpreadElement");qt$1(iA,AA,tA)}function zn(eA,AA,tA){for(let iA of eA.declarations)!iA.init||(iA.init=_$1(iA.init,AA,tA))}function qn$1(eA,AA,tA){eA.test=_$1(eA.test,AA,tA),eA.consequent=_$1(eA.consequent,AA,tA),eA.alternate=_$1(eA.alternate,AA,tA)}function Gt$1(eA,AA,tA){AA.push(Ft$1(eA,tA))}function zt$1(eA,AA,tA){let iA=eA.arguments.filter(rA=>rA.type!=="SpreadElement");Yn(iA,AA,tA),eA.callee.type==="FunctionExpression"&&Gt$1(eA.callee,AA,tA)}function jn(eA,AA,tA){eA.left.type==="MemberExpression"&&jt$1(eA.left,AA,tA),eA.right=_$1(eA.right,AA,tA)}function qt$1(eA,AA,tA){for(let iA of eA)iA=_$1(iA,AA,tA)}function jt$1(eA,AA,tA){eA.object.type==="Identifier"&&(eA.object=Ut$1(eA.object,tA)),eA.property.type!=="PrivateIdentifier"&&eA.computed&&(eA.property=_$1(eA.property,AA,tA))}function Ht$1(eA,AA,tA){eA.left=_$1(eA.left,AA,tA),eA.right=_$1(eA.right,AA,tA)}function Hn(eA,AA,tA){eA.argument=_$1(eA.argument,AA,tA)}function $t$1(eA,AA,tA){eA.left=_$1(eA.left,AA,tA),eA.right=_$1(eA.right,AA,tA)}function ft$1(eA,AA,tA){eA.test.type==="LogicalExpression"?$t$1(eA.test,AA,tA):eA.test.type==="BinaryExpression"&&Ht$1(eA.test,AA,tA),eA.consequent.type==="BlockStatement"?AA.push(new N$3(eA.consequent.body,tA)):eA.consequent.type==="IfStatement"?ft$1(eA.consequent,AA,tA):eA.consequent.type==="ReturnStatement"?dt$1(eA.consequent,AA,tA):eA.consequent.type==="ExpressionStatement"&&(eA.consequent.expression=_$1(eA.consequent.expression,AA,tA)),eA.alternate&&(eA.alternate.type==="BlockStatement"?AA.push(new N$3(eA.alternate.body,tA)):eA.alternate.type==="IfStatement"?ft$1(eA.alternate,AA,tA):eA.alternate.type==="ReturnStatement"?dt$1(eA.alternate,AA,tA):eA.alternate.type==="ExpressionStatement"&&(eA.alternate.expression=_$1(eA.alternate.expression,AA,tA)))}function $n$1(eA,AA,tA){AA.push(new N$3(eA.block.body,tA)),eA.handler&&AA.push(new N$3(eA.handler.body.body,tA))}function Xn$1(eA,AA,tA){for(let iA of eA)iA.type==="BlockStatement"?AA.push(new N$3(iA.body,tA)):iA.type==="ExpressionStatement"&&(iA.expression=_$1(iA.expression,AA,tA))}function Wn(eA,AA,tA){eA.discriminant=_$1(eA.discriminant,AA,tA);for(let iA of eA.cases)iA.test&&(iA.test=_$1(iA.test,AA,tA)),Xn$1(iA.consequent,AA,tA)}function Kn(eA,AA,tA){eA.test=_$1(eA.test,AA,tA),eA.body.type==="BlockStatement"&&AA.push(new N$3(eA.body.body,tA))}function Yn(eA,AA,tA){for(let iA of eA)iA=_$1(iA,AA,tA)}function dt$1(eA,AA,tA){!eA.argument||(eA.argument.type==="CallExpression"?"body"in eA.argument.callee&&eA.argument.callee.body.type==="BlockStatement"?AA.push(new N$3(eA.argument.callee.body.body,tA)):zt$1(eA.argument,AA,tA):eA.argument.type==="FunctionExpression"?AA.push(new N$3(eA.argument.body.body,tA)):eA.argument=_$1(eA.argument,AA,tA))}function _$1(eA,AA,tA){return eA.type==="CallExpression"?zt$1(eA,AA,tA):eA.type==="AssignmentExpression"?jn(eA,AA,tA):eA.type==="ConditionalExpression"?qn$1(eA,AA,tA):eA.type==="MemberExpression"?jt$1(eA,AA,tA):eA.type==="ArrayExpression"?Gn(eA,AA,tA):eA.type==="LogicalExpression"?$t$1(eA,AA,tA):eA.type==="BinaryExpression"?Ht$1(eA,AA,tA):eA.type==="UnaryExpression"?Hn(eA,AA,tA):eA.type==="FunctionExpression"?Gt$1(eA,AA,tA):eA.type==="SequenceExpression"?qt$1(eA.expressions,AA,tA):eA.type==="Identifier"&&(eA=Ut$1(eA,tA)),eA}function Xt$1(eA){for(let iA of eA.body)iA.type==="VariableDeclaration"&&eA.addDeclarations(iA.declarations);let AA=[],tA=eA.declaredVariables;for(let iA of eA.body)iA.type==="VariableDeclaration"?zn(iA,AA,tA):iA.type==="FunctionDeclaration"?AA.push(Ft$1(iA,tA)):iA.type==="ReturnStatement"?dt$1(iA,AA,tA):iA.type==="ExpressionStatement"?iA.expression=_$1(iA.expression,AA,tA):iA.type==="IfStatement"?ft$1(iA,AA,tA):iA.type==="TryStatement"?$n$1(iA,AA,tA):iA.type==="SwitchStatement"?Wn(iA,AA,tA):iA.type==="WhileStatement"&&Kn(iA,AA,tA);Jn(AA)}var Jn=eA=>{for(let AA of eA)Xt$1(AA)},Wt$1=eA=>{Xt$1(Fn(eA,[]))},er$1=eA=>eA.type==="ExpressionStatement"&&"directive"in eA,tr$1=eA=>/Ease and Wizz\s[0-9. ]+:/u.test(eA)?eA.replace("key(1)[1];
    ","key(1)[1].length;
    ").replace("key(1)[2];
    ","key(1)[2].length;
    "):eA,nr$1=eA=>/Khanyu\s[0-9. ]+/u.test(eA)?eA.replace("key(1)[1];
    ","key(1)[1].length;
    ").replace("key(1)[2];
    ","key(1)[2].length;
    "):eA,rr$1=eA=>{let AA=/(\/\/)?(.*) else /gu;return eA.replace(AA,`$1$2
$1 else `)},sr$1=eA=>{let AA=/(throw (["'])(?:(?=(\\?))\3[\S\s])*?\2)\s*([^;])/gu;return eA.replace(AA,`$1;
$4`)},ir$1=eA=>{let AA=/([.'"])name([\s'";
    .\)\]])/gu;
    return eA.replace(AA,"$1_name$2")
  },or$1=eA=>{
    var iA;
    let AA=eA.body[0];
    if(AA&&er$1(AA)||((iA=eA.body[0])==null?void 0:iA.type)!=="ExpressionStatement")return!1;
    let tA=eA.body[0].expression;
    return tA.type==="ArrayExpression"?!tA.elements.some(rA=>(rA==null?void 0:rA.type)!=="Literal"):eA.body[0].expression.type==="Literal"
  },ue$3=eA=>eA.operator!=="-"||eA.argument.type==="Literal"?eA:{
    arguments:[pe$3(eA.argument)],optional:!1,type:"CallExpression",callee:{
      name:"$bm_neg",type:"Identifier"
    }
  },pe$3=eA=>{
    switch(eA.type){
      case"CallExpression":return Z$3(eA),eA;
      case"BinaryExpression":return G$4(eA);
      case"UnaryExpression":return ue$3(eA);
      case"MemberExpression":return Qe$1(eA),eA;
      default:return eA
    }
  },mt$1=eA=>{
    switch(eA){
      case"+":return"$bm_sum";
      case"-":return"$bm_sub";
      case"*":return"$bm_mul";
      case"/":return"$bm_div";
      case"%":return"$bm_mod";
      default:return"$bm_sum"
    }
  },G$4=eA=>{
    if(eA.left.type==="Literal"&&eA.right.type==="Literal")return eA;
    let AA;
    return eA.operator==="instanceof"&&eA.right.type==="Identifier"&&eA.right.name==="Array"?AA={
      type:"CallExpression",arguments:[eA.left],optional:!1,callee:{
        name:"$bm_isInstanceOfArray",type:"Identifier"
      }
    }:["+","-","*","/","%"].includes(eA.operator)?AA={
      arguments:[pe$3(eA.left),pe$3(eA.right)],optional:!1,type:"CallExpression",callee:{
        name:mt$1(eA.operator),type:"Identifier"
      }
    }:AA={
      arguments:[pe$3(eA.left),pe$3(eA.right)],optional:!1,type:"CallExpression",callee:{
        name:mt$1(eA.operator),type:"Identifier"
      }
    },AA
  };
  function Ze$1(eA){
    eA.test.type==="BinaryExpression"&&(eA.test=G$4(eA.test)),eA.consequent.type==="AssignmentExpression"?Le$1(eA.consequent):eA.consequent.type==="BinaryExpression"?eA.consequent=G$4(eA.consequent):eA.consequent.type==="SequenceExpression"?Se$4(eA.consequent.expressions):eA.consequent.type==="CallExpression"?Z$3(eA.consequent):eA.consequent.type==="LogicalExpression"&&fe$3(eA.consequent),eA.alternate.type==="AssignmentExpression"?Le$1(eA.alternate):eA.alternate.type==="BinaryExpression"?eA.alternate=G$4(eA.alternate):eA.alternate.type==="SequenceExpression"?Se$4(eA.alternate.expressions):eA.alternate.type==="CallExpression"?Z$3(eA.alternate):eA.alternate.type==="LogicalExpression"&&fe$3(eA.alternate)
  }function Qe$1(eA){
    eA.property.type==="BinaryExpression"?eA.property=G$4(eA.property):eA.property.type==="UnaryExpression"?eA.property=ue$3(eA.property):eA.property.type==="CallExpression"&&Z$3(eA.property),eA.object.type==="BinaryExpression"?eA.object=G$4(eA.object):eA.object.type==="UnaryExpression"?eA.object=ue$3(eA.object):eA.object.type==="CallExpression"&&Z$3(eA.object)
  }var Ie$2=eA=>{
    eA.expression.type==="CallExpression"?Z$3(eA.expression):eA.expression.type==="BinaryExpression"?eA.expression=G$4(eA.expression):eA.expression.type==="UnaryExpression"?eA.expression=ue$3(eA.expression):eA.expression.type==="AssignmentExpression"?Le$1(eA.expression):eA.expression.type==="ConditionalExpression"?Ze$1(eA.expression):eA.expression.type==="SequenceExpression"?Se$4(eA.expression.expressions):eA.expression.type==="LogicalExpression"&&fe$3(eA.expression)
  },Kt$1=eA=>{
    eA.test.type==="BinaryExpression"&&(eA.test=G$4(eA.test)),eA.consequent.type==="BlockStatement"?F$1(eA.consequent.body):eA.consequent.type==="ExpressionStatement"?Ie$2(eA.consequent):eA.consequent.type==="ReturnStatement"&&eA.consequent.argument&&pe$3(eA.consequent.argument),eA.alternate&&(eA.alternate.type==="IfStatement"?Kt$1(eA.alternate):eA.alternate.type==="BlockStatement"?F$1(eA.alternate.body):eA.alternate.type==="ExpressionStatement"&&Ie$2(eA.alternate))
  },ar$1=eA=>{
    eA.body.type==="BlockStatement"?F$1(eA.body.body):eA.body.type==="ExpressionStatement"&&Ie$2(eA.body),eA.test.type==="MemberExpression"&&Qe$1(eA.test)
  },cr$1=eA=>{
    eA.body.type==="BlockStatement"?F$1(eA.body.body):eA.body.type==="ExpressionStatement"&&Ie$2(eA.body)
  },lr$1=eA=>{
    for(let AA of eA.body.body)AA.type==="MethodDefinition"&&F$1(AA.value.body.body)
  },pr$1=eA=>{
    eA.callee.type==="ClassExpression"&&lr$1(eA.callee)
  },ur$1=eA=>{
    eA.body.type!=="BlockStatement"&&(eA.body=Je$2(eA.body))
  },fr$2=eA=>{
    for(let AA of eA.declarations)!AA.init||(AA.init.type==="BinaryExpression"?AA.init=G$4(AA.init):AA.init.type==="UnaryExpression"?AA.init=ue$3(AA.init):AA.init.type==="CallExpression"?Z$3(AA.init):AA.init.type==="ConditionalExpression"?Ze$1(AA.init):AA.init.type==="LogicalExpression"?fe$3(AA.init):AA.init.type==="NewExpression"?pr$1(AA.init):AA.init.type==="ArrowFunctionExpression"&&ur$1(AA.init))
  },dr$1=eA=>{
    F$1(eA.block.body),eA.handler&&F$1(eA.handler.body.body)
  },mr$1=eA=>{
    for(let AA of eA.cases)F$1(AA.consequent)
  },F$1=eA=>{
    for(let AA of eA)AA.type==="ExpressionStatement"?Ie$2(AA):AA.type==="IfStatement"?Kt$1(AA):AA.type==="FunctionDeclaration"?F$1(AA.body.body):AA.type==="WhileStatement"?ar$1(AA):AA.type==="ForStatement"?cr$1(AA):AA.type==="VariableDeclaration"?fr$2(AA):AA.type==="ReturnStatement"&&AA.argument?AA.argument=pe$3(AA.argument):AA.type==="TryStatement"?dr$1(AA):AA.type==="SwitchStatement"&&mr$1(AA)
  },Se$4=eA=>{
    for(let AA of eA)if(AA.type==="CallExpression")Z$3(AA);
    else if(AA.type==="BinaryExpression")AA=G$4(AA);
    else if(AA.type==="UnaryExpression")AA=ue$3(AA);
    else if(AA.type==="AssignmentExpression")Le$1(AA);
    else if(AA.type==="ConditionalExpression")Ze$1(AA);
    else if(AA.type==="MemberExpression")Qe$1(AA);
    else if(AA.type==="ArrayExpression"){
      let tA=AA.elements.filter(iA=>(iA==null?void 0:iA.type)!=="SpreadElement");
      Se$4(tA)
    }else AA.type==="LogicalExpression"&&fe$3(AA)
  },Z$3=eA=>{
    let AA=eA.arguments.filter(tA=>tA.type!=="SpreadElement");
    Se$4(AA),eA.callee.type==="Identifier"&&eA.callee.name==="eval"?AA[0]={
      type:"MemberExpression",computed:!0,object:{
        type:"ArrayExpression",elements:AA.slice(0,1)
      },optional:!1,property:{
        value:0,type:"Literal",raw:"0"
      }
    }:eA.callee.type==="FunctionExpression"&&F$1(eA.callee.body.body)
  };
  function hr$1(eA){
    let AA=[];
    eA.left.type==="MemberExpression"&&AA.push(eA.left),AA.push(eA.right),eA.right={
      type:"CallExpression",arguments:AA,optional:!1,callee:{
        name:mt$1(eA.operator.slice(0,1)),type:"Identifier"
      }
    },eA.operator="="
  }var Le$1=eA=>{
    (eA.operator==="+="||eA.operator==="-=")&&hr$1(eA),eA.right=Je$2(eA.right)
  },fe$3=eA=>{
    eA.right=Je$2(eA.right),eA.left=Je$2(eA.left)
  },Je$2=eA=>{
    if(eA.type==="BinaryExpression")eA=G$4(eA);
    else if(eA.type==="UnaryExpression")eA=ue$3(eA);
    else if(eA.type==="CallExpression")Z$3(eA);
    else if(eA.type==="MemberExpression")Qe$1(eA);
    else if(eA.type==="ConditionalExpression")Ze$1(eA);
    else if(eA.type==="ArrayExpression"){
      let AA=eA.elements.filter(tA=>(tA==null?void 0:tA.type)!=="SpreadElement");
      Se$4(AA)
    }else eA.type==="FunctionExpression"?F$1(eA.body.body):eA.type==="LogicalExpression"&&fe$3(eA);
    return eA
  },Yt$1=eA=>{
    for(let AA of eA)AA.type==="ExpressionStatement"?AA.expression.type==="CallExpression"?AA.expression.arguments=AA.expression.arguments.map(tA=>tA.type==="AssignmentExpression"?tA.right:tA):AA.expression.type==="AssignmentExpression"?Le$1(AA.expression):AA.expression.type==="LogicalExpression"&&fe$3(AA.expression):AA.type==="FunctionDeclaration"&&Yt$1(AA.body.body)
  },Jt$1=eA=>{
    let AA=tr$1(eA);
    AA=nr$1(AA),AA=rr$1(AA),AA=sr$1(AA),AA=ir$1(AA),AA=Ot$1(AA);
    let tA=esprimaExports.parseScript(AA,{
      tokens:!0,range:!0
    });
    if(or$1(tA))return(0,eval)(AA);
    Yt$1(tA.body),AA.includes("use javascript")||F$1(tA.body),Wt$1(tA.body),ce$3(tA.body);
    try{
      return AA=escodegenExports.generate(tA),AA=`var $bm_rt;
      
${
        AA
      }`,AA
    }catch(iA){
      return console.error("Expression conversion error",iA),""
    }
  },Zt$1="__$Ex";
  function Qt$1(eA,AA,tA,iA){
    let rA=null,gA=0,nA=new Array(tA.length).fill(0),oA=new Array(iA.length).fill(0);
    for(let sA=0;
    sA<200;
    sA+=1){
      let aA=[],IA=sA/199,CA=0;
      for(let EA=0;
      EA<tA.length;
      EA+=1){
        nA[EA]=eA[EA]+tA[EA],oA[EA]=AA[EA]+iA[EA];
        let BA=eA[EA]+(nA[EA]-eA[EA])*IA,lA=nA[EA]+(oA[EA]-nA[EA])*IA,QA=oA[EA]+(AA[EA]-oA[EA])*IA,cA=BA+(lA-BA)*IA,uA=lA+(QA-lA)*IA,dA=cA+(uA-cA)*IA;
        aA.push(dA),rA!==null&&(CA+=(aA[EA]-rA[EA])**2)
      }CA=Math.sqrt(CA),gA+=CA,rA=aA
    }return gA
  }function en$1(eA){
    let AA=eA.parent;
    for(;
    AA&&!(AA instanceof K$4);
    )AA=AA.parent;
    if(!AA)throw new Error("Parent layer not found");
    return AA
  }function tn(eA){
    let AA=eA.parent;
    for(;
    AA&&!(AA instanceof le$4||AA instanceof _e$4);
    )AA=AA.parent;
    if(!AA)throw new Error("Parent composition not found");
    return AA
  }var ht$1=(eA,AA,tA)=>{
    let iA=Math.hypot(eA.x-AA.x,eA.y-AA.y),rA=Math.hypot(AA.x-tA.x,AA.y-tA.y),gA=Math.hypot(tA.x-eA.x,tA.y-eA.y),nA=Math.acos((iA**2+rA**2-gA**2)/(2*iA*rA));
    return Math.abs(nA*(180/Math.PI)-90)<.01
  },sn=eA=>{
    if(eA.isAnimated||eA.value.vertices.length!==4||eA.value.inTangents.some(tA=>tA.x!==0||tA.y!==0)||eA.value.outTangents.some(tA=>tA.x!==0||tA.y!==0))return!1;
    let AA=eA.value.vertices;
    return ht$1(AA[0],AA[1],AA[2])&&ht$1(AA[1],AA[2],AA[3])&&ht$1(AA[2],AA[3],AA[0])
  },yt$1=eA=>{
    let AA=eA.shapes,tA,iA;
    for(let rA=AA.length-1;
    rA>=0;
    rA-=1){
      let gA=AA[rA];
      if(gA instanceof Bt$2&&gA.mergeMode===Uo.INTERSECT&&rA>0){
        let nA=AA[rA-1];
        if(nA instanceof gt$2&&sn(nA.shape))tA=nA;
        else if(nA instanceof pe$5){
          let oA=nA.shapes[nA.shapes.length-1];
          oA instanceof gt$2&&sn(oA.shape)&&(tA=nA,iA=gA)
        }
      }else gA instanceof pe$5&&yt$1(gA)
    }tA&&eA.removeChild(tA),iA&&eA.removeChild(iA)
  },De$4=(eA,AA,tA)=>new h$7($$5(eA.x,AA.x,tA),$$5(eA.y,AA.y,tA));
  function an(eA,AA,tA,iA,rA){
    let gA=eA,nA=AA,oA=tA,sA=iA,aA=De$4(gA,nA,rA),IA=De$4(nA,oA,rA),CA=De$4(oA,sA,rA),EA=De$4(aA,IA,rA),BA=De$4(IA,CA,rA),lA=De$4(EA,BA,rA);
    return gA.x===nA.x&&gA.y===nA.y&&oA.x===sA.x&&oA.y===sA.y?{
      c1:[gA,gA,lA,lA],c2:[lA,lA,sA,sA]
    }:{
      c1:[gA,aA,EA,lA],c2:[lA,BA,CA,sA]
    }
  }function cn$1(eA,AA){
    let tA=eA.inTangents.length,iA=eA.isClosed,rA=tA,gA=iA?rA:rA-1,nA=AA-tA,oA=new Array(rA).fill(0);
    if(gA<=0){
      eA.setVertices(Array(nA).fill([0,0])),eA.setOutTangents(Array(nA).fill([0,0])),eA.setInTangents(Array(nA).fill([0,0]));
      return
    }let sA=Math.floor(nA/gA),aA=nA%gA;
    for(let lA=0;
    lA<gA;
    lA+=1)oA[lA]=sA+(lA<aA?1:0);
    let IA=0,CA=[],EA=[],BA=[];
    for(let lA=0;
    lA<rA;
    lA+=1)if(oA[lA]===0)CA.push(new h$7(se$4(eA.vertices[lA].x,3),se$4(eA.vertices[lA].y,3))),BA.push(new h$7(se$4(eA.outTangents[lA].x,3),se$4(eA.outTangents[lA].y,3))),lA===rA-1?EA[0]=new h$7(se$4(eA.inTangents[0].x,3),se$4(eA.inTangents[0].y,3)):EA[IA+1]=new h$7(se$4(eA.inTangents[lA+1].x,3),se$4(eA.inTangents[lA+1].y,3)),IA+=1;
    else{
      let QA,cA,uA,dA;
      lA===rA-1&&iA?(QA=eA.vertices[lA],cA=new h$7(eA.outTangents[lA].x+eA.vertices[lA].x,eA.outTangents[lA].y+eA.vertices[lA].y),uA=new h$7(eA.inTangents[0].x+eA.vertices[0].x,eA.inTangents[0].y+eA.vertices[0].y),dA=eA.vertices[0]):(QA=eA.vertices[lA],cA=new h$7(eA.outTangents[lA].x+eA.vertices[lA].x,eA.outTangents[lA].y+eA.vertices[lA].y),uA=new h$7(eA.inTangents[lA+1].x+eA.vertices[lA+1].x,eA.inTangents[lA+1].y+eA.vertices[lA+1].y),dA=eA.vertices[lA+1]);
      let fA=oA[lA]+1,yA=an(QA,cA,uA,dA,1/fA);
      for(let wA=0;
      wA<fA;
      wA+=1)wA<fA-1?(yA=an(QA,cA,uA,dA,1/(fA-wA)),CA.push(new h$7(se$4(yA.c1[0].x,3),se$4(yA.c1[0].y,3))),BA.push(new h$7(se$4(yA.c1[1].x-yA.c1[0].x,3),se$4(yA.c1[1].y-yA.c1[0].y,3))),IA===AA-1?EA[0]=new h$7(se$4(yA.c2[2].x-yA.c2[0].x,3),se$4(yA.c2[2].y-yA.c2[0].y,3)):EA[IA+1]=new h$7(se$4(yA.c1[2].x-yA.c1[3].x,3),se$4(yA.c1[2].y-yA.c1[3].y,3)),QA=yA.c2[0],cA=yA.c2[1],uA=yA.c2[2],dA=yA.c2[3]):(CA.push(new h$7(se$4(yA.c2[0].x,3),se$4(yA.c2[0].y,3))),BA.push(new h$7(se$4(yA.c2[1].x-yA.c2[0].x,3),se$4(yA.c2[1].y-yA.c2[0].y,3))),IA===AA-1?EA[0]=new h$7(se$4(yA.c2[2].x-yA.c2[3].x,3),se$4(yA.c2[2].y-yA.c2[3].y,3)):EA[IA+1]=new h$7(se$4(yA.c2[2].x-yA.c2[3].x,3),se$4(yA.c2[2].y-yA.c2[3].y,3))),IA+=1
    }eA.setVertices(CA),eA.setOutTangents(BA),eA.setInTangents(EA)
  }function ln(eA){
    let AA=[],tA=[],iA=[],rA=eA.vertices.length,gA=0;
    eA.isClosed&&(AA.push(eA.vertices[0]),tA.push(eA.outTangents[0]),iA.push(eA.inTangents[0]),gA=1);
    let nA=rA-1;
    for(let sA=gA;
    sA<rA;
    sA+=1)AA.push(eA.vertices[nA]),tA.push(eA.outTangents[nA]),iA.push(eA.inTangents[nA]),nA-=1;
    let oA=new z$4(AA,tA,iA);
    return oA.setIsClosed(eA.isClosed),oA
  }var H$4=class{
    getProperty(AA,tA,iA=[]){
      let rA=tA[AA];
      if(typeof rA=="function")return rA.bind(tA)(...iA);
      if(rA===void 0){
        let gA=ct$1(AA,tA);
        if(gA)return gA
      }return rA
    }setProperty(AA,tA,iA){
      let rA=`set${
        AA.charAt(0).toUpperCase()
      }${
        AA.slice(1)
      }`,gA=tA[rA];
      if(typeof gA=="function"){
        gA.bind(tA)(iA);
        return
      }let nA=tA[AA];
      if(nA instanceof Ve$4){
        nA.setValue(iA);
        return
      }let oA=ct$1(AA,tA);
      if(oA){
        oA.setValue(iA);
        return
      }tA[AA]=iA
    }expectType(AA,tA){
      if(AA.constructor.name!==tA.name)throw new Error(`Expected ${
        tA.name
      }, got ${
        AA.constructor.name
      }`);
      return AA
    }
  },et$1=class{
    constructor(AA,tA,iA){
      l$4(this,"scene"),l$4(this,"comp"),l$4(this,"parentMap",new Map),l$4(this,"matteParentMap",new Map),l$4(this,"layers",new Map),l$4(this,"assets",new Map),l$4(this,"is3d",!1),l$4(this,"parent"),this.scene=AA,this.comp=tA,this.parent=iA,this.parent&&(this.assets=this.parent.assets)
    }mark3d(){
      this.is3d=!0,this.parent&&this.parent.mark3d()
    }parentLayer(AA){
      let tA=this.layers.get(AA);
      return tA||console.warn("Could not find parent layer"),tA
    }resolve(){
      for(let[AA,tA]of this.layers.entries()){
        let iA=this.parentMap.get(AA);
        if(iA){
          let gA=this.parentLayer(iA);
          gA&&(gA.setData("isParentLayer",!0),tA.setParent(gA))
        }let rA=this.matteParentMap.get(AA);
        if(rA){
          let gA=this.parentLayer(rA);
          gA.setIsHidden(!1),gA.setIsTrackMatte(!0),tA.setTrackMatteParent(gA)
        }
      }
    }
  },Te$4=class extends H$4{
    constructor(AA,tA=iA=>({
      
    })){
      super(),this.prop=AA,this.defaults=tA
    }apply(AA,tA,iA){
      let rA=this.getProperty(this.prop,tA);
      if(rA===void 0)return;
      if(!(AA instanceof R$2))throw new Error("Expected property group");
      this.setProperty("matchName",rA,iA.matchName),this.setProperty("name",rA,tA.name),this.setProperty("isHidden",rA,tA.visible);
      let gA=this.defaults(AA);
      for(let[nA,oA]of Object.entries(gA))this.setProperty(nA,rA,oA);
      this.applyProperties(AA,rA,iA.converter)
    }applyProperties(AA,tA,iA){
      iA.applyProperties(AA,tA)
    }
  },z$2=class extends H$4{
    apply(AA,tA,iA){
      iA.converter.applyProperties(AA,tA)
    }
  },Re$3=class extends H$4{
    apply(AA,tA,iA){
      
    }
  },A$3=class extends Re$3{
    
  },Me$4=class extends A$3{
    
  },tt$2=class extends Me$4{
    
  },B$5=class extends H$4{
    constructor(AA,tA){
      super(),this.prop=AA,this.map=tA
    }apply(AA,tA,iA){
      if(!(AA instanceof O$3))throw new Error("Expected enum property");
      let rA=iA.converter.propertyStaticValue(AA);
      rA!==void 0&&this.setProperty(this.prop,tA,this.convert(rA))
    }convert(AA){
      let tA=this.expectType(AA,h$7).x;
      if(this.map===void 0)return tA;
      let iA=this.map[tA];
      if(iA===void 0)throw new Error(`Unknown enum value: ${
        tA
      }`);
      return iA
    }
  },V$4=class extends H$4{
    constructor(AA,tA=(rA,gA)=>({
      
    }),iA=""){
      super(),this.Ctor=AA,this.defaults=tA,this.valueProp=iA
    }apply(AA,tA,iA){
      let rA=AA;
      if(!(tA instanceof L$5))throw new Error("Not a node");
      if(this.valueProp!==""&&(rA=this.getProperty(this.valueProp,rA)),!(rA instanceof R$2))throw new Error("Not a group");
      if(!iA.importOptions.exportHiddenLayers&&!iA.importOptions.includeHiddenLayers&&!rA.visible)return;
      let gA=new this.Ctor(tA);
      this.setProperty("name",gA,rA.name),this.setProperty("isHidden",gA,iA.importOptions.exportHiddenLayers?!1:!rA.visible),this.setProperty("matchName",gA,iA.matchName);
      let nA=this.defaults(AA,rA);
      for(let[oA,sA]of Object.entries(nA))this.setProperty(oA,gA,sA);
      iA.converter.applyProperties(rA,gA)
    }
  },Et$1=class extends H$4{
    apply(AA,tA,iA){
      return iA.converter.convertEffectParade(AA,tA)
    }
  },br$1={
    trimMode:ui$1.SIMULTANEOUSLY,trimOffset:new M$4(0),trimStart:new ae$4(0),trimEnd:new ae$4(100)
  },pn={
    strokeWidth:new v$7(2),lineCapType:ko$2.BUTT,lineJoinType:Mo$1.MITER,miterLimit:new v$7(4)
  },un={
    fillRule:Vo$1.NONZERO,endPoint:new h$7(100,0),gradient:new lt$2([{
      stop:new v$7(0),color:I$4.from("white")
    },{
      stop:new v$7(1),color:I$4.from("black")
    }])
  },wr$1={
    "ADBE Tint":Js.TINT,"ADBE Fill":Js.FILL,"ADBE Stroke":Js.STROKE,"ADBE Tritone":Js.TRITONE,"ADBE Pro Levels2":Js.PRO_LEVELS,"ADBE Drop Shadow":Js.DROP_SHADOW,"ADBE Radial Wipe":Js.RADIAL_WIPE,"ADBE Displacement Map":Js.DISPLACEMENT_MAP,"ADBE Set Matte3":Js.MATTE3,"ADBE Gaussian Blur 2":Js.GAUSSIAN_BLUR,"ADBE Twirl":Js.TWIRL,"ADBE MESH WARP":Js.MESH_WARP,"ADBE Ripple":Js.WAVY,"ADBE Spherize":Js.SPHERIZE,"ADBE FreePin3":Js.PUPPET
  },kt$1=class extends H$4{
    constructor(AA,tA,iA=1){
      super(),this.ctor=AA,this.prop=tA,this.multiplier=iA
    }apply(AA,tA,iA){
      let rA=this.getProperty(this.prop,tA);
      if(rA!==void 0)if(AA instanceof O$3)this.onProperty(AA,rA,iA);
      else throw new Error("Expected property")
    }convert(AA,tA){
      return this.doConvert(AA,tA)
    }doConvert(AA,tA){
      let iA=this.ctor.name;
      switch(iA){
        case v$7.name:return AA instanceof se$2?new v$7(AA.layerId):typeof AA=="number"?new v$7(AA*this.multiplier):new v$7(se$4(this.expectType(AA,h$7).x*this.multiplier,3));
        case h$7.name:let rA=this.expectType(AA,h$7).scaleToClone(this.multiplier);
        return new h$7(se$4(rA.x,3),se$4(rA.y,3),rA.is3D?se$4(rA.z,3):null);
        case I$4.name:return this.expectType(AA,I$4);
        case k$7.name:let gA=this.expectType(AA,h$7).scaleToClone(this.multiplier);
        return new k$7(se$4(gA.x,3),se$4(gA.y,3));
        case M$4.name:return new M$4(se$4(this.expectType(AA,h$7).x*this.multiplier,3));
        case ae$4.name:return new ae$4(se$4(this.expectType(AA,h$7).x*this.multiplier,3));
        case z$4.name:return te$2.convertBezier(this.expectType(AA,Ee$3),tA);
        case lt$2.name:return te$2.convertGradient(this.expectType(AA,ke$3));
        case It$2.name:return te$2.convertTextDocument(this.expectType(AA,ge$2),tA);
        default:throw new Error(`Unknown property type ${
          iA
        }`)
      }
    }
  },p$6=class extends kt$1{
    onProperty(AA,tA,iA){
      if(!(tA instanceof we$4))throw new Error("Expected animated property");
      tA instanceof ve$4&&AA.split&&(tA.switchToSplitMode(AA.components===3),iA.matchName==="ADBE Position")||iA.converter.convertAnimatedProperty(AA,tA,this)
    }setKeyframe(AA,tA,iA){
      var QA;
      let{
        timeStretch:rA,timelineOffset:gA
      }=en$1(tA),nA=tn(tA).timeline.frameRate,oA=AA.keyframes[iA],sA=this.convert(oA.value,tA),aA=AA.keyframes[(iA+1)%AA.keyframes.length],IA=this.convert(aA.value,tA),CA=Math.abs(aA.time-oA.time)/Math.abs(rA),EA=se$4(oA.time*rA*nA+gA,3),BA,lA;
      if(AA.type===2){
        if(rA<0){
          let cA=new h$7(-oA.inTangent.y,oA.inTangent.x),uA=new h$7(-aA.outTangent.y,aA.outTangent.x);
          BA=Pe$3(sA,cA),lA=Pe$3(IA,uA)
        }else BA=Pe$3(sA,oA.outTangent),lA=Pe$3(IA,aA.inTangent);
        BA.equals(lA)&&(BA=void 0,lA=void 0)
      }if(oA.transitionType===3)tA.setValueAtKeyFrame(sA,EA,new st$1);
      else if(oA.transitionType===1&&aA.transitionType===1||lt$1(CA,0))tA instanceof ve$4?tA.setValueAtKeyFrame(sA,EA,new Ae$3,BA,lA):tA.setValueAtKeyFrame(sA,EA,new Ae$3);
      else if(AA.type===2||AA.type===1){
        let cA=Array.isArray(aA.inInfluence)?aA.inInfluence[0]:aA.inInfluence,uA=Array.isArray(aA.inSpeed)?aA.inSpeed[0]:aA.inSpeed,dA=Array.isArray(oA.outInfluence)?oA.outInfluence[0]:oA.outInfluence,fA=Array.isArray(oA.outSpeed)?oA.outSpeed[0]:oA.outSpeed,yA;
        AA.type===1?yA=100:yA=Qt$1([sA.x,sA.y],[IA.x,IA.y],[oA.outTangent.x,oA.outTangent.y],[aA.inTangent.x,aA.inTangent.y]);
        let wA=yA/CA,MA,pA;
        yA===0||fA===0||uA===0?(MA=dA,pA=cA):(MA=Math.min(yA/(fA*CA),dA),pA=Math.min(yA/(uA*CA),cA));
        let RA=new h$7,NA=new h$7;
        RA.setX(se$4(1-pA,3)),NA.setX(se$4(MA,3)),lt$1(wA,0)?(RA.setY(RA.x),NA.setY(NA.x)):(RA.setY(se$4(1-uA/wA*pA,3)),NA.setY(se$4(fA/wA*MA,3))),tA instanceof ve$4?tA.setValueAtKeyFrame(sA,EA,new F$2(NA,RA),BA,lA):tA.setValueAtKeyFrame(sA,EA,new F$2(NA,RA))
      }else{
        let cA=[],uA=[],dA=[],fA=[],yA=bA=>{
          if(bA instanceof v$7||bA instanceof ae$4||bA instanceof M$4)return[bA.value];
          if(bA instanceof I$4){
            let OA=bA.red+bA.green+bA.blue;
            return[OA,OA,OA]
          }return bA instanceof k$7?[bA.width,bA.height]:[bA.x,bA.y,bA.is3D?bA.z:0]
        },wA=yA(sA),MA=yA(IA),pA=(bA,OA,WA)=>{
          let $A=[...bA];
          for(;
          $A.length<OA;
          )$A.push($A[0]??WA);
          return $A
        },RA=bA=>bA instanceof M$4||bA instanceof ae$4||bA instanceof v$7||bA instanceof k$7||this.prop==="scale"&&tA.parent instanceof pe$5?1/100:1,NA=RA(IA),LA=RA(sA),HA=pA(aA.inInfluence,AA.components,0),KA=pA(oA.outInfluence,AA.components,0),TA=pA(Array.isArray(aA.inSpeed)?aA.inSpeed.map(bA=>bA*NA):[aA.inSpeed*NA],AA.components,0),SA=pA(Array.isArray(oA.outSpeed)?oA.outSpeed.map(bA=>bA*LA):[oA.outSpeed*LA],AA.components,0);
        for(let bA=0;
        bA<AA.components;
        bA+=1){
          cA.push(se$4(1-HA[bA],3)),uA.push(se$4(KA[bA],3));
          let OA=MA[bA]-wA[bA];
          AA.type===0&&(OA*=255),Math.abs(OA)<1e-7&&(OA=1);
          let WA=SA[bA]*KA[bA]*100,$A=TA[bA]*HA[bA]*100;
          fA.push(se$4(WA*(CA/OA),3)),dA.push(se$4(1-$A*CA/OA,3))
        }let xA=new h$7(cA[0],dA[0]),vA=new h$7(uA[0],fA[0]),_A=new h$7(cA[1],dA[1]),kA=new h$7(uA[1],fA[1]),YA=new h$7(cA[2],dA[2]),wi=new h$7(uA[2],fA[2]);
        tA instanceof ve$4||tA instanceof B$6?(tA.switchToSplitMode(sA.is3D),tA.x.setValueAtKeyFrame(new v$7(sA.x),EA,new F$2(vA,xA)),tA.y.setValueAtKeyFrame(new v$7(sA.y),EA,new F$2(kA,_A)),sA.is3D&&((QA=tA.z)==null||QA.setValueAtKeyFrame(new v$7(sA.z),EA,new F$2(wi,YA)))):tA.setValueAtKeyFrame(sA,EA,new F$2(vA,xA))
      }
    }
  },nt$1=class extends Te$4{
    constructor(AA,tA="transform"){
      super(tA),l$4(this,"_converters"),this._converters={
        
      };
      for(let[iA,rA]of Object.entries(nt$1._suffixes))this._converters[nt$1._prefix+AA+iA]=rA;
      AA===""&&(this._converters["ADBE Scale"]=new p$6(h$7,"scale",100))
    }applyProperties(AA,tA,iA){
      if(!(tA instanceof Nr$1))throw new Error("Expected transform");
      iA.applyProperties(AA,tA,this._converters)
    }
  },de$4=nt$1;
  l$4(de$4,"_prefix","ADBE "),l$4(de$4,"_suffixes",{
    "Anchor Point":new p$6(h$7,"anchorPoint"),"Anchor Point 3D":new p$6(h$7,"anchorPoint"),Anchor:new p$6(h$7,"anchorPoint"),Position:new p$6(h$7,"position"),"Position 3D":new p$6(h$7,"position"),Position_0:new p$6(v$7,"position.x"),Position_1:new p$6(v$7,"position.y"),Position_2:new p$6(v$7,"position.z"),Scale:new p$6(h$7,"scale"),"Scale 3D":new p$6(h$7,"scale"),Opacity:new p$6(ae$4,"opacity",100),Orientation:new p$6(h$7,"orientation"),"Rotate X":new p$6(M$4,"rotationX"),"Rotation X":new p$6(M$4,"rotationX"),"Rotate Y":new p$6(M$4,"rotationY"),"Rotation Y":new p$6(M$4,"rotationY"),"Rotate Z":new p$6(M$4,"rotationZ"),"Rotation Z":new p$6(M$4,"rotationZ"),Rotation:new p$6(M$4,"rotation"),Skew:new p$6(M$4,"skew"),"Skew Axis":new p$6(M$4,"skewAxis")
  });
  var ee$4=class{
    constructor(AA,tA,iA=[]){
      this.EffectValueClass=AA,this.converter=tA,this.args=iA
    }apply(AA,tA,iA,rA){
      let gA=new this.EffectValueClass(rA,...this.args);
      gA.setName(AA.name),gA.setMatchName(AA.matchName),this.converter&&iA.convertAnimatedProperty(tA,gA.value,this.converter)
    }
  },gt$1=class extends p$6{
    constructor(){
      super(v$7,""),l$4(this,"_strokeTypeToName",{
        [Wo$1.Dash]:"dash",[Wo$1.Gap]:"gap",[Wo$1.Offset]:"offset"
      })
    }apply(AA,tA){
      if(!(tA instanceof je$4||tA instanceof We$3))throw new Error("Expected stroke shape");
      if(!(AA instanceof R$2))throw new Error("Expected property group for stroke dashes");
      for(let iA of AA.properties){
        let rA=this._getStrokeDashType(iA.matchName);
        if(!rA)continue;
        let gA=tA.createStrokeDash();
        gA.setStrokeDashType(rA),gA.setName(this._strokeTypeToName[rA]);
        let nA=iA.value;
        if(nA.animated){
          gA.strokeDashLength.setIsAnimated(!0);
          for(let oA=0;
          oA<nA.keyframes.length;
          oA+=1)this.setKeyframe(nA,gA.strokeDashLength,oA)
        }else nA.value&&gA.strokeDashLength.setStaticValue(this.convert(nA.value,tA))
      }
    }_getStrokeDashType(AA){
      if(AA.startsWith("ADBE Vector Stroke Dash"))return Wo$1.Dash;
      if(AA.startsWith("ADBE Vector Stroke Gap"))return Wo$1.Gap;
      if(AA==="ADBE Vector Stroke Offset")return Wo$1.Offset
    }
  },At$1=class extends p$6{
    constructor(){
      super(It$2,"")
    }apply(AA,tA){
      if(!(tA instanceof er$2))throw new Error("Expected text layer");
      if(!(AA instanceof Ae$2))throw new Error("Expected text property group for text document");
      let iA=AA.fonts.map(rA=>this._getOrCreateFontAsset(rA,tA.scene).name);
      if(tA.textData.setData("TEXT_LAYER_FONTS",iA),AA.documents.animated){
        tA.textData.setIsAnimated(!0);
        for(let rA=0;
        rA<AA.documents.keyframes.length;
        rA+=1)this.setKeyframe(AA.documents,tA.textData,rA)
      }else if(AA.documents.value){
        let rA=AA.documents.value,gA=this.convert(rA,tA.textData);
        tA.textData.setStaticValue(gA)
      }
    }_getOrCreateFontAsset(AA,tA){
      let iA=tA.fonts.find(rA=>rA.name===AA.family);
      return iA||(iA=new Qe$2(tA),iA.setFamily(AA.family),iA.setName(AA.family),iA)
    }
  },xt$1=class extends H$4{
    apply(AA,tA,iA){
      if(tA instanceof le$4)for(let rA of AA.keyframes){
        let gA=rA.value,nA=tA.scene.timeline.frameRate,oA=tA.createMarker();
        oA.setComment(gA.name),oA.setStartFrame(se$4(rA.time*nA,3)),oA.setDurationInFrames(se$4(gA.duration*nA,3))
      }
    }
  },Sr$1={
    "ADBE Root Vectors Group":new z$2,"ADBE Layer Styles":new Me$4,"ADBE Transform Group":new de$4(""),"ADBE Extrsn Options Group":new A$3,"ADBE Material Options Group":new A$3,"ADBE Audio Group":new tt$2,"ADBE Layer Sets":new A$3,"ADBE Time Remapping":new p$6(v$7,"timeMapping"),"ADBE Effect Parade":new Et$1,"ADBE Marker":new xt$1,"ADBE Camera Options Group":new z$2,"ADBE Camera Aperture":new p$6(v$7,"perspective"),"ADBE Camera Zoom":new A$3,"ADBE Mask Parade":new z$2,"ADBE Mask Atom":new V$4(Nt$2,eA=>{
      let AA=eA;
      return{
        mode:AA.mode,index:AA.index,isInverted:AA.inverted
      }
    },"properties"),"ADBE Mask Shape":new p$6(z$4,"shape"),"ADBE Mask Offset":new p$6(v$7,"expansion"),"ADBE Mask Opacity":new p$6(ae$4,"opacity",100),"ADBE Mask Feather":new A$3,"ADBE Plane Options Group":new A$3,"ADBE Data Group":new A$3,"ADBE Layer Overrides":new A$3,"ADBE Source Options Group":new A$3,"ADBE Text Properties":new z$2,"ADBE Text Document":new At$1,"ADBE Text Animators":new z$2,"ADBE Text Animator":new V$4(Qt$2),"ADBE Text More Options":new z$2,"ADBE Text Anchor Point Option":new B$5("textGrouping"),"ADBE Text Anchor Point Align":new p$6(h$7,"textAlignment"),"ADBE Text Render Order":new A$3,"ADBE Text Character Blend Mode":new A$3,"ADBE Text Selectors":new z$2,"ADBE Text Selector":new Te$4("textSelector",()=>({
      expressionSelector:new v$7(100)
    })),"ADBE Text Percent Start":new p$6(v$7,"start"),"ADBE Text Percent End":new p$6(v$7,"end"),"ADBE Text Percent Offset":new p$6(v$7,"offset"),"ADBE Text Index Start":new p$6(v$7,"start"),"ADBE Text Index End":new p$6(v$7,"end"),"ADBE Text Index Offset":new p$6(v$7,"offset"),"ADBE Text Range Advanced":new z$2,"ADBE Text Selector Mode":new tt$2,"ADBE Text Selector Max Amount":new p$6(v$7,"maxAmount"),"ADBE Text Range Units":new B$5("rangeUnits"),"ADBE Text Range Shape":new B$5("shape"),"ADBE Text Selector Smoothness":new p$6(v$7,"expressionSelector"),"ADBE Text Levels Min Ease":new p$6(v$7,"minEase"),"ADBE Text Levels Max Ease":new p$6(v$7,"maxEase"),"ADBE Text Range Type2":new B$5("basedOn"),"ADBE Text Randomize Order":new B$5("randomize",{
      0:!1,1:!0
    }),"ADBE Text Random Seed":new Re$3,"ADBE Text Animator Properties":new Te$4("transform"),"ADBE Text Opacity":new p$6(ae$4,"opacity"),"ADBE Text Scale 3D":new p$6(h$7,"scale"),"ADBE Text Position 3D":new p$6(h$7,"position"),"ADBE Text Rotation":new p$6(M$4,"rotation"),"ADBE Text Fill Color":new p$6(I$4,"fillColor"),"ADBE Text Fill Opacity":new p$6(ae$4,"fillOpacity"),"ADBE Text Fill Hue":new p$6(M$4,"hue"),"ADBE Text Fill Saturation":new p$6(ae$4,"saturation"),"ADBE Text Fill Brightness":new p$6(ae$4,"brightness"),"ADBE Text Stroke Hue":new p$6(M$4,"hue"),"ADBE Text Stroke Saturation":new p$6(ae$4,"saturation"),"ADBE Text Stroke Brightness":new p$6(ae$4,"brightness"),"ADBE Text Stroke Color":new p$6(I$4,"strokeColor"),"ADBE Text Stroke Opacity":new p$6(ae$4,"strokeOpacity"),"ADBE Text Stroke Width":new p$6(v$7,"strokeWidth"),"ADBE Text Line Spacing":new p$6(v$7,"lineHeight"),"ADBE Text Line Anchor":new A$3,"ADBE Text Track Type":new A$3,"ADBE Text Tracking Amount":new p$6(v$7,"textTracking"),"ADBE Text Character Replace":new A$3,"ADBE Text Character Offset":new A$3,"ADBE Text Blur":new A$3,"ADBE Text Path Options":new Te$4("maskedPath",eA=>{
      var tA;
      let AA=(tA=eA.properties.find(iA=>iA.matchName==="ADBE Text Path"))==null?void 0:tA.value;
      return AA?{
        maskIndex:AA.value
      }:{
        
      }
    }),"ADBE Text Path":new Re$3,"ADBE Text Reverse Path":new p$6(v$7,"reversePath"),"ADBE Text Perpendicular To Path":new p$6(v$7,"perpendicularToPath"),"ADBE Text Force Align Path":new p$6(v$7,"forceAlignment"),"ADBE Text First Margin":new p$6(v$7,"firstMargin"),"ADBE Text Last Margin":new p$6(v$7,"lastMargin"),"ADBE Opacity":new p$6(ae$4,"opacity",100),"ADBE Vector Group Opacity":new p$6(ae$4,"opacity"),"ADBE Vector Repeater Opacity 1":new p$6(ae$4,"startOpacity"),"ADBE Vector Repeater Opacity 2":new p$6(ae$4,"endOpacity"),"ADBE Vector Repeater Start Opacity":new p$6(ae$4,"startOpacity",100),"ADBE Vector Repeater End Opacity":new p$6(ae$4,"endOpacity",100),"ADBE Envir Appear in Reflect":new A$3,"ADBE Vector Group":new V$4(pe$5),"ADBE Vector Blend Mode":new B$5("blendMode",It$1),"ADBE Vectors Group":new z$2,"ADBE Vector Transform Group":new de$4("Vector "),"ADBE Vector Materials Group":new A$3,"ADBE Vector Shape - Rect":new V$4(Ze$2,()=>({
      size:new k$7(100,100)
    })),"ADBE Vector Shape Direction":new B$5("direction",{
      1:Ho$1.NORMAL,2:Ho$1.NORMAL,3:Ho$1.REVERSED
    }),"ADBE Vector Rect Position":new p$6(h$7,"position"),"ADBE Vector Rect Size":new p$6(k$7,"size"),"ADBE Vector Rect Roundness":new p$6(v$7,"roundness"),"ADBE Vector Shape - Ellipse":new V$4(Xe$3,()=>({
      size:new k$7(100,100)
    })),"ADBE Vector Ellipse Position":new p$6(h$7,"position"),"ADBE Vector Ellipse Size":new p$6(k$7,"size"),"ADBE Vector Ellipse Roundness":new p$6(v$7,"roundness"),"ADBE Vector Shape - Star":new V$4(qe$3,()=>({
      starType:Ko$1.Star,numPoints:new v$7(5),innerRadius:new v$7(50),outerRadius:new v$7(100)
    })),"ADBE Vector Star Type":new B$5("starType"),"ADBE Vector Star Points":new p$6(v$7,"numPoints"),"ADBE Vector Star Position":new p$6(h$7,"position"),"ADBE Vector Star Rotation":new p$6(M$4,"rotation"),"ADBE Vector Star Inner Radius":new p$6(v$7,"innerRadius"),"ADBE Vector Star Outer Radius":new p$6(v$7,"outerRadius"),"ADBE Vector Star Inner Roundess":new p$6(v$7,"innerRoundness"),"ADBE Vector Star Outer Roundess":new p$6(v$7,"outerRoundness"),"ADBE Vector Shape - Group":new V$4(gt$2),"ADBE Vector Shape":new p$6(z$4,"shape"),"ADBE Vector Graphic - Fill":new V$4(Gt$2,()=>({
      color:new I$4(255,0,0),fillRule:Vo$1.NONZERO
    })),"ADBE Vector Fill Color":new p$6(I$4,"color"),"ADBE Vector Fill Opacity":new p$6(ae$4,"opacity"),"ADBE Vector Fill Rule":new B$5("fillRule"),"ADBE Vector Composite Order":new Me$4,"ADBE Vector Graphic - Stroke":new V$4(je$4,()=>({
      ...pn,color:new I$4(255,255,255)
    })),"ADBE Vector Stroke Color":new p$6(I$4,"color"),"ADBE Vector Stroke Opacity":new p$6(ae$4,"opacity"),"ADBE Vector Stroke Width":new p$6(v$7,"strokeWidth"),"ADBE Vector Stroke Line Cap":new B$5("lineCapType"),"ADBE Vector Stroke Line Join":new B$5("lineJoinType"),"ADBE Vector Stroke Miter Limit":new p$6(v$7,"miterLimit"),"ADBE Vector Stroke Dashes":new gt$1,"ADBE Vector Stroke Taper":new A$3,"ADBE Vector Stroke Wave":new A$3,"ADBE Vector Graphic - G-Fill":new V$4(vt$2,()=>({
      ...un
    })),"ADBE Vector Graphic - G-Stroke":new V$4(We$3,()=>({
      ...pn,...un
    })),"ADBE Vector Grad Start Pt":new p$6(h$7,"startPoint"),"ADBE Vector Grad End Pt":new p$6(h$7,"endPoint"),"ADBE Vector Grad HiLite Length":new p$6(v$7,"highlightLength"),"ADBE Vector Grad HiLite Angle":new p$6(M$4,"highlightAngle"),"ADBE Vector Grad Colors":new p$6(lt$2,"gradient"),"ADBE Vector Grad Type":new B$5("gradientType"),"ADBE Vector Filter - Merge":new V$4(Bt$2),"ADBE Vector Merge Type":new B$5("mergeMode"),"ADBE Vector Filter - Offset":new V$4(Yt$2),"ADBE Vector Offset Amount":new p$6(v$7,"amount"),"ADBE Vector Offset Line Join":new B$5("lineJoinType"),"ADBE Vector Offset Miter Limit":new p$6(v$7,"miterLimit"),"ADBE Vector Filter - PB":new V$4($t$2),"ADBE Vector PuckerBloat Amount":new p$6(v$7,"amount"),"ADBE Vector Filter - Repeater":new V$4(Xt$2),"ADBE Vector Repeater Transform":new de$4("Vector Repeater "),"ADBE Vector Repeater Copies":new p$6(v$7,"copies"),"ADBE Vector Repeater Offset":new p$6(v$7,"offset"),"ADBE Vector Repeater Order":new B$5("copyCompositeType"),"ADBE Vector Filter - RC":new V$4(Wt$2),"ADBE Vector RoundCorner Radius":new p$6(v$7,"roundness"),"ADBE Vector Filter - Trim":new V$4(Zt$2,()=>br$1),"ADBE Vector Trim Type":new B$5("trimMultipleShapes"),"ADBE Vector Trim Start":new p$6(ae$4,"trimStart"),"ADBE Vector Trim End":new p$6(ae$4,"trimEnd"),"ADBE Vector Trim Offset":new p$6(M$4,"trimOffset"),"ADBE Vector Filter - Twist":new V$4(qt$2),"ADBE Vector Twist Angle":new p$6(M$4,"twistAmount"),"ADBE Vector Twist Center":new p$6(h$7,"twistCenter"),"ADBE Vector Filter - Roughen":new A$3,"ADBE Vector Roughen Size":new A$3,"ADBE Vector Roughen Detail":new A$3,"ADBE Vector Roughen Points":new A$3,"ADBE Vector Temporal Freq":new A$3,"ADBE Vector Correlation":new A$3,"ADBE Vector Temporal Phase":new A$3,"ADBE Vector Spatial Phase":new A$3,"ADBE Vector Random Seed":new A$3,"ADBE Vector Filter - Wiggler":new A$3,"ADBE Vector Xform Temporal Freq":new A$3,"ADBE Vector Wiggler Transform":new A$3,"ADBE Vector Filter - Zigzag":new V$4(Xr$1),"ADBE Vector Zigzag Size":new p$6(v$7,"amplitude"),"ADBE Vector Zigzag Detail":new p$6(v$7,"numPoints"),"ADBE Vector Zigzag Points":new p$6(v$7,"pointType"),"ADBE Effect Built In Params":new A$3,"ADBE Effect Mask Opacity":new A$3,"ADBE Paint Group":new A$3
  },te$2=class{
    constructor(AA,tA){
      l$4(this,"_layerIndex",1),l$4(this,"_project"),l$4(this,"_importOptions"),this._project=AA,this._importOptions={
        defaultNames:!1,enableNodeIds:!0,includeHiddenLayers:!1,exportGuideLayers:!1,exportHiddenLayers:!1,excludeExpressions:!1,...tA
      }
    }_isValidAssetId(AA){
      return Number.isInteger(AA)&&AA>0&&AA<=Number.MAX_SAFE_INTEGER
    }_getAssetSafely(AA){
      if(this._isValidAssetId(AA))return this._project.assets.get(AA)
    }convertScene(AA){
      let tA=new ci$1({
        enableNodeIds:this._importOptions.enableNodeIds
      }).createScene();
      return this._compToScene(AA,tA),tA.allLayers.concat(tA.assets.flatMap(iA=>iA instanceof _e$4?iA.allLayers:[])).forEach(iA=>{
        var gA,nA;
        let rA=iA.getData("isParentLayer");
        if(!this._importOptions.exportHiddenLayers&&!this._importOptions.includeHiddenLayers&&!rA&&iA.isHidden){
          iA.removeFromGraph();
          return
        }if(iA.isGuide){
          rA?(iA.setIsHidden(!this._importOptions.exportGuideLayers),!this._importOptions.exportGuideLayers&&iA instanceof be$4&&iA.clearShapes()):this._importOptions.exportGuideLayers||iA.removeFromGraph();
          return
        }if(iA instanceof Pt$1||iA instanceof lr$2||iA instanceof cr$2){
          let oA=iA instanceof lr$2?((gA=iA.asset)==null?void 0:gA.width)??1:iA.width,sA=iA instanceof lr$2?((nA=iA.asset)==null?void 0:nA.height)??1:iA.height;
          iA.masks.forEach(aA=>{
            aA.shape.values.forEach(IA=>{
              IA instanceof z$4&&IA.points.forEach(CA=>{
                CA.forEach(EA=>{
                  EA.setX(se$4(EA.x*oA,3)),EA.setY(se$4(EA.y*sA,3))
                })
              })
            })
          })
        }else if(iA instanceof er$2){
          let oA=iA.masks.findIndex(sA=>sA.index===iA.maskedPath.maskIndex);
          if(oA===-1)return;
          iA.maskedPath.setMaskIndex(oA)
        }else iA instanceof be$4&&yt$1(iA)
      }),tA
    }_compToScene(AA,tA){
      tA.setName(AA.name),tA.setWidth(AA.width),tA.setHeight(AA.height),tA.timeline.setFrameRate(AA.framerate),tA.timeline.setStartAndEndFrame(AA.inTime,AA.outTime),tA.timeline.setCurrentFrame(AA.playheadTime),tA.setBackgroundColor(AA.color);
      let iA=new et$1(tA,AA,void 0);
      for(let rA of AA.layers)this._convertLayer(rA,tA,iA);
      tA.setIs3D(iA.is3d),iA.resolve(),AA.markers&&this.applyProperties(AA.markers.properties,tA)
    }_convertLayer(AA,tA,iA){
      if(AA.parentId&&iA.parentMap.set(AA.id,AA.parentId),AA.isNull){
        let rA=new Jr$1(tA);
        this._avLayerCommon(AA,rA,iA),rA.anchorPoint.updateValues(gA=>new h$7(gA.x*100,gA.y*100,gA.is3D?gA.y*100:null))
      }else this._isValidAssetId(AA.assetId)&&(this._handleImageSequenceLayers(AA),this._convertAssetLayer(AA,tA,iA));
      switch(AA.type){
        case 4:this._avLayerCommon(AA,new be$4(tA),iA);
        break;
        case 3:this._avLayerCommon(AA,new er$2(tA),iA);
        break;
        case 2:this._layerCommon(AA,new Fr$1(tA),iA);
        break;
        case 1:this._layerCommon(AA,new Ur(tA),iA);
        break
      }
    }_layerCommon(AA,tA,iA){
      if(tA.setId(AA.id.toString()),!AA.name&&this._importOptions.defaultNames){
        let oA=this._getDefaultLayerName(AA,tA);
        tA.setName(oA),this._layerIndex+=1
      }else tA.setName(AA.name);
      tA.setIsGuide(AA.isGuide),tA.setIsHidden(this._importOptions.exportHiddenLayers?!1:!AA.visible),tA.setTimeStretch(se$4(AA.timeStretch,3));
      let rA=AA.startTime*iA.comp.framerate;
      tA.setTimelineOffset(se$4(rA,3));
      let gA=AA.inTime*AA.timeStretch*iA.comp.framerate+rA,nA=AA.outTime*AA.timeStretch*iA.comp.framerate+rA;
      AA.timeStretch<0&&([gA,nA]=[nA,gA]),tA.setStartAndEndFrame(se$4(gA,3),se$4(nA,3),!0),tA instanceof X$4&&(iA.is3d=AA.threedimensional,tA.setIs3d(AA.threedimensional),AA.threedimensional&&tA.transform.initialize3DRotation(),AA.isAdjustment&&tA.setOpacity(new ae$4(0))),this.applyProperties(AA.properties,tA),iA.layers.set(AA.id,tA),iA.parentMap.set(AA.id,AA.parentId)
    }_avLayerCommon(AA,tA,iA){
      var nA,oA;
      tA.setPosition(new h$7(iA.comp.width/2,iA.comp.height/2,AA.threedimensional?0:null)),this._layerCommon(AA,tA,iA),tA.setCollapseTransformation(AA.continuouslyRasterize),tA.setAutoOrient(AA.autoOrient);
      let rA=Lt$1[AA.blendMode]??Do$1.NORMAL;
      if(tA.setBlendMode(rA),!AA.matteMode||AA.matteId===0)return;
      let gA=(nA=iA.comp.layers.find(sA=>sA.id===AA.matteId))==null?void 0:nA.id;
      if(!gA){
        let sA=iA.comp.layers.findIndex(aA=>aA.id===AA.id)-1;
        gA=(oA=iA.comp.layers[sA])==null?void 0:oA.id
      }!gA||(tA.setTrackMatteType(AA.matteMode),iA.matteParentMap.set(AA.id,gA))
    }_handleImageSequenceLayers(AA){
      let tA=this._getAssetSafely(AA.assetId);
      if(!AA.name&&tA&&(AA.name=tA.name),tA instanceof W$3&&tA.sequenceInfo&&tA.sequenceInfo.count>0){
        let iA=new q$3;
        iA.name=`${
          tA.name
        } Sequence`,iA.width=tA.width,iA.height=tA.height,iA.framerate=1,iA.inTime=AA.startTime,iA.outTime=AA.outTime;
        let rA=oA=>this._project.assets.has(oA)?rA(oA+1):oA,gA=[],nA=new Map([...this._project.assets.values()].filter(oA=>oA instanceof W$3).map(oA=>[oA.fullPath,oA]));
        for(let oA=0;
        oA<tA.sequenceInfo.count;
        oA+=1){
          let[sA,aA]=tA.name.split("."),IA=(tA.sequenceInfo.start+oA).toString().padStart(tA.sequenceInfo.maxLength,"0"),CA=`${
            sA
          }${
            IA
          }.${
            aA
          }`,EA=`${
            tA.fullPath
          }\\${
            CA
          }`,BA=nA.get(EA);
          if(BA){
            gA.push(BA);
            continue
          }let lA=rA(oA+1),QA=new W$3(lA,CA,EA,tA.width,tA.height);
          gA.push(QA),this._project.assets.set(QA.id,QA)
        }for(let[oA,sA]of gA.entries()){
          let aA=structuredClone(AA);
          aA.id=oA+1,aA.parentId=0,aA.matteId=0,aA.matteMode=0,aA.name=sA.name,aA.assetId=sA.id,aA.startTime=0,aA.inTime=oA,aA.outTime=oA+1,aA.properties=new R$2,iA.layers.push(aA)
        }this._project.assets.set(AA.assetId,iA)
      }
    }_convertAssetLayer(AA,tA,iA){
      let rA=this._getAssetSafely(AA.assetId);
      if(rA instanceof ye$4){
        let gA=new cr$2(tA);
        gA.setWidth(rA.width),gA.setHeight(rA.height),gA.setSolidColor(rA.color),gA.setAnchor(new h$7(.5,.5,AA.threedimensional?0:null)),this._avLayerCommon(AA,gA,iA),gA.anchorPoint.updateValues(nA=>new h$7(nA.x*gA.width,nA.y*gA.height,AA.threedimensional?0:null))
      }else{
        let gA=this._convertAsset(AA.assetId,iA);
        if(gA instanceof Ne$3){
          let nA=new lr$2(tA);
          nA.setImage(gA),nA.setAnchor(new h$7(.5,.5,AA.threedimensional?0:null)),this._avLayerCommon(AA,nA,iA),nA.anchorPoint.updateValues(oA=>new h$7(oA.x*gA.width,oA.y*gA.height,AA.threedimensional?0:null))
        }else if(gA instanceof Le$2){
          let nA=new pr$2(tA);
          nA.setSound(gA),this._layerCommon(AA,nA,iA)
        }else if(gA instanceof _e$4&&rA instanceof q$3){
          let nA=new Pt$1(tA);
          nA.setPrecomposition(gA),nA.setSize(new k$7(rA.width,rA.height)),nA.setAnchor(new h$7(.5,.5,AA.threedimensional?0:null)),this._avLayerCommon(AA,nA,iA),nA.anchorPoint.updateValues(oA=>new h$7(oA.x*nA.width,oA.y*nA.height,AA.threedimensional?0:null)),nA.timeMapping.isAnimated||nA.timeMapping.setStaticValue(null)
        }else throw new Error("Unknown asset type")
      }
    }_convertAsset(AA,tA){
      let iA=tA.assets.get(AA);
      if(iA!==void 0)return iA;
      let rA=this._getAssetSafely(AA);
      if(rA===void 0)throw new Error(`Asset ${
        AA
      } not found`);
      if(rA instanceof W$3)if(rA.width>0&&rA.height>0){
        let gA=tA.scene.createImageAsset();
        return gA.setWidth(rA.width),gA.setHeight(rA.height),gA.setPath(rA.fullPath),tA.assets.set(AA,gA),gA
      }else{
        let gA=tA.scene.createSoundAsset();
        return gA.setPath(rA.fullPath),tA.assets.set(AA,gA),gA
      }else if(rA instanceof q$3){
        let gA=tA.comp.framerate/rA.framerate;
        gA!==1&&rA.scale(gA,this._project.assets);
        let nA=this._compToPrecomp(rA,tA);
        return tA.assets.set(AA,nA),nA
      }throw new Error("Unknown asset type")
    }_compToPrecomp(AA,tA){
      let iA=new _e$4(tA.scene);
      iA.setFrameRate(AA.framerate),iA.setName(AA.name),iA.setBackgroundColor(AA.color);
      let rA=new et$1(tA.scene,AA,tA);
      for(let gA of AA.layers)this._convertLayer(gA,iA,rA);
      return iA.setIs3D(tA.is3d),rA.resolve(),iA
    }applyProperties(AA,tA,iA={
      
    }){
      for(let rA of AA.properties){
        let gA=Sr$1[rA.matchName];
        gA===void 0&&(gA=iA[rA.matchName]),gA!==void 0?gA.apply(rA.value,tA,{
          converter:this,matchName:rA.matchName,importOptions:this._importOptions
        }):console.warn(`Unsupported match name: ${
          rA.matchName
        }`)
      }
    }static convertGradient(AA){
      let tA=[];
      AA.colorStops.forEach((gA,nA)=>{
        if(tA.push(new K$3(gA.offset,gA.midPoint,gA.value.clone())),nA<AA.colorStops.length-1){
          let oA=AA.colorStops[nA+1],sA=gA.offset+(oA.offset-gA.offset)*gA.midPoint,aA=gA.value.red+(oA.value.red-gA.value.red)*.5,IA=gA.value.green+(oA.value.green-gA.value.green)*.5,CA=gA.value.blue+(oA.value.blue-gA.value.blue)*.5;
          tA.push(new K$3(sA,.5,new I$4(aA,IA,CA)))
        }
      });
      let iA=[];
      AA.alphaStops.forEach((gA,nA)=>{
        if(iA.push(gA),nA<AA.alphaStops.length-1){
          let oA=AA.alphaStops[nA+1],sA=gA.offset+(oA.offset-gA.offset)*gA.midPoint,aA=gA.value+(oA.value-gA.value)*.5;
          iA.push(new K$3(sA,.5,aA))
        }
      });
      let rA=new lt$2;
      for(let gA of tA)rA.addColor(gA.value,se$4(gA.offset,3));
      if(iA.every(gA=>gA.value===1))return rA;
      for(let gA of iA)rA.addAlpha(new v$7(se$4(gA.value,3)),se$4(gA.offset,3));
      return rA
    }static bezierPoint(AA,tA){
      let iA=AA.points[tA];
      return new h$7($$5(AA.minimum.x,AA.maximum.x,iA.x),$$5(AA.minimum.y,AA.maximum.y,iA.y))
    }static convertBezier(AA,tA){
      let iA=[],rA=[],gA=[];
      for(let oA=0;
      oA<AA.points.length-2;
      oA+=3){
        let sA=oA===0?AA.points.length-1:oA-1,aA=this.bezierPoint(AA,oA);
        aA.setX(se$4(aA.x,3)),aA.setY(se$4(aA.y,3));
        let IA=this.bezierPoint(AA,oA+1).subtractToClone(aA);
        IA.setX(se$4(IA.x,3)),IA.setY(se$4(IA.y,3));
        let CA=this.bezierPoint(AA,sA).subtractToClone(aA);
        CA.setX(se$4(CA.x,3)),CA.setY(se$4(CA.y,3)),iA.push(aA),gA.push(IA),rA.push(CA)
      }let nA=new z$4(iA,rA,gA);
      return nA.setIsClosed(AA.closed),AA.groupInfo.bezierCount>1&&nA.points.length<AA.groupInfo.maxVertexCount&&cn$1(nA,AA.groupInfo.maxVertexCount),tA instanceof yt$2&&tA.parent instanceof gt$2&&tA.parent.direction===Ho$1.REVERSED&&(nA=ln(nA)),nA
    }static convertTextDocument(AA,tA){
      let iA=tA.getData("TEXT_LAYER_FONTS"),{
        characterStyles:rA,lineStyles:gA,paragraphStyles:nA,text:oA
      }=AA,sA=new It$2(oA.replaceAll(`
`,"\r").trimEnd());
      return gA[0]&&sA.setJustify(gA[0].textJustify),rA[0]&&(sA.setFontName(iA[rA[0].fontIndex]),sA.setFontColor(rA[0].fillColor),sA.setFontSize(rA[0].size),sA.setLineHeight(rA[0].leadingAuto?rA[0].size*1.2:rA[0].leading),sA.setTextTracking(rA[0].tracking),rA[0].strokeEnabled&&(sA.setStrokeColor(rA[0].strokeColor),sA.setStrokeWidth(rA[0].strokeWidth))),nA[0]&&(sA.setBoxSize(nA[0].wrapSize),sA.setBoxPosition(nA[0].wrapPosition)),sA
    }propertyStaticValue(AA){
      var tA;
      return AA.value!==void 0?AA.value:(tA=AA.keyframes[0])==null?void 0:tA.value
    }convertAnimatedProperty(AA,tA,iA){
      var rA;
      if(AA.expression&&(this._importOptions.excludeExpressions?(rA=tA.scene)==null||rA.setData(AA.key,tA):tA.setData(Zt$1,Jt$1(AA.expression))),!AA.animated&&AA.value){
        tA.setStaticValue(iA.convert(AA.value,tA));
        return
      }tA.setIsAnimated(!0);
      for(let gA=0;
      gA<AA.keyframes.length;
      gA+=1)iA.setKeyframe(AA,tA,gA)
    }_getEffectValueConverter(AA){
      return AA.type===2||AA.type===10?new ee$4(Ir$1,new p$6(v$7,"value"),[bt$1.SLIDER]):AA.type===4||AA.type===7?new ee$4(Ir$1,new p$6(v$7,"value"),[bt$1.DROPDOWN]):AA.type===5?new ee$4(wr$2,new p$6(I$4,"value"),[bt$1.COLOR]):AA.type===12?new ee$4(Ir$1,new p$6(v$7,"value"),[bt$1.LAYER]):AA.type===6||AA.type===18?new ee$4(Lr$1,new p$6(h$7,"value"),[bt$1.POINT]):new ee$4(Rr$1)
    }convertEffectParade(AA,tA){
      for(let iA of AA.properties){
        if(!(iA.value instanceof xe$2))throw new Error("Expected effect instance");
        let rA=this._project.effects.get(iA.matchName);
        if(rA===void 0)throw new Error("Effect definition not found");
        let gA=new zt$2(tA,wr$1[iA.matchName]??Js.CUSTOM);
        gA.setName(iA.value.name?iA.value.name:rA.name),gA.setIsEnabled(iA.value.parameters.visible);
        for(let nA of rA.parameters){
          if(!nA.name)continue;
          let oA=iA.value.parameters.property(nA.matchName);
          oA instanceof O$3||(oA=new O$3,oA.value=nA.lastValue??nA.defaultValue),this._getEffectValueConverter(nA).apply(nA,oA,this,gA)
        }
      }
    }_getDefaultLayerName(AA,tA){
      if(AA.isNull)return`Null ${
        this._layerIndex
      }`;
      if(AA.isAdjustment)return`Adjustment Layer ${
        this._layerIndex
      }`;
      if(tA instanceof X$4)return TD(tA,this._layerIndex);
      switch(AA.type){
        case 4:return`Shape Layer ${
          this._layerIndex
        }`;
        case 3:return`Text Layer ${
          this._layerIndex
        }`;
        case 2:return`Camera ${
          this._layerIndex
        }`;
        case 1:return`Light Layer ${
          this._layerIndex
        }`;
        case 0:return`Asset Layer ${
          this._layerIndex
        }`;
        default:return`Layer ${
          this._layerIndex
        }`
      }
    }
  },mn=class extends bp{
    constructor(){
      super(...arguments),l$4(this,"author","LottieFiles"),l$4(this,"capabilities",[Jo$1.IMPORTER,Jo$1.MULTI_SCENE_IMPORTER]),l$4(this,"description","Imports AEP Files"),l$4(this,"email","support@lottiefiles.com"),l$4(this,"id","com.lottiefiles.aep"),l$4(this,"title","AEP Importer"),l$4(this,"url","https://www.lottiefiles.com/")
    }async importScene(eA){
      if(!eA)return new le$4;
      let{
        compId:AA,compName:tA,data:iA,importOptions:rA
      }=eA,gA=new Be$3(iA),nA=new we$3(gA.endianness).parseProject(gA.parse()),oA=new te$2(nA,rA),sA;
      return AA?sA=nA.compositions.find(aA=>aA.id===AA):tA?sA=nA.compositions.find(aA=>aA.name===tA):sA=nA.compositions[0],sA?oA.convertScene(sA):new le$4
    }async importScenes(eA){
      if(!eA)return[];
      let{
        data:AA,importOptions:tA
      }=eA,iA=new Be$3(AA),rA=new we$3(iA.endianness).parseProject(iA.parse()),gA=new te$2(rA,tA);
      return rA.compositions.map(nA=>gA.convertScene(nA))
    }
  },E$5=Object.defineProperty,I$2=(eA,AA,tA)=>AA in eA?E$5(eA,AA,{
    enumerable:!0,configurable:!0,writable:!0,value:tA
  }):eA[AA]=tA,o$3=(eA,AA,tA)=>(I$2(eA,typeof AA!="symbol"?AA+"":AA,tA),tA),m$6=class{
    constructor(AA){
      o$3(this,"endianness",new ie$2),o$3(this,"_dom"),this._dom=new DOMParser$1().parseFromString(AA,"text/xml")
    }parse(){
      return this._convertElement(this._dom.documentElement)
    }_convertElement(AA){
      let tA=new Q$3(AA.tagName,0,void 0);
      if(AA.hasAttribute("bdata")){
        let iA=AA.getAttribute("bdata");
        AA.tagName==="cdat"&&(iA=iA.replace(/00000000/gu,"0000000000000000")),tA.length=iA.length/2,tA.data=iA.length===0?new Uint8Array:Uint8Array.from(iA.match(/.{
          2
        }/g).map(rA=>parseInt(rA,16)))
      }else if(AA.tagName==="string")tA.header="Utf8",tA.data=AA.textContent??"";
      else if(AA.tagName==="fileReference"){
        let iA={
          
        };
        for(let rA of AA.attributes)rA.name==="target_is_folder"?iA.target_is_folder=rA.value==="1"||rA.value.toLowerCase()==="true":iA[rA.name]=rA.value;
        tA.header="alas",tA.data=JSON.stringify(iA)
      }else{
        tA.header="LIST";
        let iA=AA.tagName==="Pin"?"Pin ":AA.tagName;
        tA.data=new oe$2(iA);
        for(let rA=AA.firstElementChild;
        rA;
        rA=rA.nextElementSibling)tA.data.children.push(this._convertElement(rA))
      }return tA
    }
  },b$6=class extends bp{
    constructor(){
      super(...arguments),o$3(this,"author","LottieFiles"),o$3(this,"capabilities",[Jo$1.IMPORTER,Jo$1.MULTI_SCENE_IMPORTER]),o$3(this,"description","Imports AEPX Files"),o$3(this,"email","support@lottiefiles.com"),o$3(this,"id","com.lottiefiles.aepx"),o$3(this,"title","AEPX Importer"),o$3(this,"url","https://www.lottiefiles.com/")
    }async importScene(AA){
      if(!AA)return new le$4;
      let{
        compId:tA,compName:iA,importOptions:rA,xmlString:gA
      }=AA,nA=new m$6(gA),oA=new we$3(nA.endianness).parseProject(nA.parse()),sA=new te$2(oA,rA),aA;
      return tA?aA=oA.compositions.find(IA=>IA.id===tA):iA?aA=oA.compositions.find(IA=>IA.name===iA):aA=oA.compositions[0],aA?sA.convertScene(aA):new le$4
    }async importScenes(AA){
      if(!AA)return[];
      let{
        importOptions:tA,xmlString:iA
      }=AA,rA=new m$6(iA),gA=new we$3(rA.endianness).parseProject(rA.parse()),nA=new te$2(gA,tA);
      return gA.compositions.map(oA=>nA.convertScene(oA))
    }
  },browserPonyfill$1={
    exports:{
      
    }
  },browserPonyfill=browserPonyfill$1.exports,hasRequiredBrowserPonyfill;
  function requ

// ====== MAIN BUNDLE: Import Integration ======

:n,addThemes:s,addSlotToThemes:r,fontLoaderActor:o
});
return i?(V.endAction(),{
  asset:i.asset,nodeId:i.asset.nodeId
}):(V.endAction(),null)
}catch(i){
  throw V.rollbackAction(),i
}
},DJ=async({
  toolkit:e,svgString:t,name:n
})=>{
  try{
    V.beginAction();
    const{
      asset:s,sceneSize:r
    }=await Tk({
      toolkit:e,svgString:t,name:n
    });
    return pC(s,r),V.endAction(),{
      asset:s,nodeId:s.nodeId
    }
  }catch(s){
    throw V.rollbackAction(),s
  }
},QJ=e=>e==="AEP"?wB.id:bB.id,PJ=e=>{
  const t={
    importOptions:{
      defaultNames:!0,enableNodeIds:!0
    }
  };
  return e.format==="AEP"?{
    ...t,data:e.data
  }:{
    ...t,xmlString:e.xmlString
  }
},_J=async(e,t)=>{
  const n=await e.export(Ta.id,{
    scene:t,removeUnusedAssets:!0
  });
  return t.removeFromGraph(),typeof n=="string"?JSON.parse(n):n
},Nk=async({
  toolkit:e,json:t,addSlotToThemes:n
})=>{
  const s=await e.import(Ta.id,{
    animation:t,enableNodeIds:!0,standardizeTimeline:!1,recalculateStartEnd:!1
  });
  if(!s)throw new Error("Failed to import Lottie JSON as scene");
  return s.slots.forEach(r=>fA(r)),yc(s,e),s.slots.forEach(r=>n(r)),s
},Bk=async(e,t)=>{
  const n=PJ(t),s=QJ(t.format),r=await e.importMultipleScenes(s,n);
  if(!r.length)throw new Error(`No compositions found in ${
    t.format
  } file`);
  const o=[];
  for(const i of r)o.push(await _J(e,i));
  return o
},UJ=async({
  toolkit:e,input:t,activeScene:n,selectedNodeId:s,onLayerCreate:r,onLayersSelect:o,onImportComplete:i,setTimelineForFpsChange:A,addSlotToThemes:l,importPosition:d,wrapInPrecomposition:u=!0,fontLoaderActor:h
})=>{
  const f=await Bk(e,t);
  try{
    V.beginAction();
    for(let g=1;
    g<f.length;
    g++)await Nk({
      toolkit:e,json:f[g],addSlotToThemes:l
    });
    V.endAction()
  }catch(g){
    throw V.rollbackAction(),g
  }await Ax({
    toolkit:e,json:f[0],activeScene:n,selectedNodeId:s,onLayerCreate:r,onLayersSelect:o,onImportComplete:i,setTimelineForFpsChange:A,addSlotToThemes:l,importPosition:d,fontLoaderActor:h,wrapInPrecomposition:u
  })
},GJ=async({
  toolkit:e,input:t,name:n,addSlotToThemes:s,fontLoaderActor:r
})=>{
  const o=await Bk(e,t);
  for(let i=1;
  i<o.length;
  i++)await Nk({
    toolkit:e,json:o[i],addSlotToThemes:s
  });
  return cx({
    toolkit:e,json:o[0],name:n,addSlotToThemes:s,fontLoaderActor:r
  })
},YJ=async({
  toolkit:e,input:t,name:n,addSlotToThemes:s,fontLoaderActor:r
})=>{
  try{
    V.beginAction();
    const{
      asset:o
    }=await GJ({
      toolkit:e,input:t,name:n,addSlotToThemes:s,fontLoaderActor:r
    });
    return V.endAction(),{
      asset:o,nodeId:o.nodeId
    }
  }catch(o){
    throw V.rollbackAction(),o
  }
},Mk=20,HJ=e=>{
  const t=e.lastIndexOf(".");
  return t>0?e.slice(0,t):e
},Rk=e=>e.type===rn.SVG||/\.svg$/iu.exec(e.name),WJ=e=>/\.lottie$/iu.exec(e.name),kk=e=>e.type===rn.JSON||/\.json$/iu.exec(e.name),vk=e=>e.type===rn.PNG||e.type===rn.JPEG||e.type===rn.WEBP||/\.(png|jpg|jpeg|webp)$/iu.exec(e.name),Fk=e=>e.type===rn.TTF||e.type==="application/x-font-ttf"||e.type===rn.OctetStream&&/\.ttf$/iu.exec(e.name)||/\.ttf$/iu.exec(e.name),QE=e=>/\.aep$/iu.exec(e.name),Lk=e=>/\.aepx$/iu.exec(e.name),Ok=e=>/\.creator$/iu.exec(e.name),PE=e=>!Rk(e)&&!WJ(e)&&!kk(e)&&!vk(e)&&!Fk(e)&&!QE(e)&&!Lk(e)&&!Ok(e),G0=(e,t)=>e.size>1e3*1e3*Mk;
function jk(e,t){
  if(!t.includes(e))return e;
  let n=1,s=`${
    e
  }_${
    n
  }`;
  for(;
  t.includes(s);
  )n+=1,s=`${
    e
  }_${
    n
  }`;
  return s
}const VJ=(e,t)=>{
  const n=K(t,p.ThemeManager),r=n.getSnapshot().context.themes.find(o=>o.id===Vl);
  e.forEach(o=>{
    r==null||r.slots.for

// ---

omposition
});
o+=1,at({
  system:n,data:{
    eventType:ce.AssetAdded,parameters:{
      source:m.source,type:"svg"
    }
  }
})
}catch{
  r+=1
}
}else if(vk(P))try{
  if(m.importToAssetsOnly){
    const se=await LJ({
      toolkit:C,imageFile:P,name:_
    });
    se&&H.push(se.nodeId)
  }else await vJ({
    toolkit:C,imageFile:P,name:_,activeScene:S.scene,onLayerCreate:Ae,onLayersSelect:G,selectedNodeId:Z,importPosition:$
  });
  o+=1,at({
    system:n,data:{
      eventType:ce.AssetAdded,parameters:{
        source:m.source,type:"image"
      }
    }
  })
}catch{
  r+=1
}else if(Fk(P))try{
  const se=await FJ({
    toolkit:C,fontFile:P,name:_
  });
  se&&(H.push(se.nodeId),z.send({
    type:"FONT.CACHE_FONT",fontAsset:se.asset
  })),o+=1,at({
    system:n,data:{
      eventType:ce.AssetAdded,parameters:{
        source:m.source,type:"font"
      }
    }
  })
}catch{
  r+=1
}else if(QE(P)||Lk(P)){
  const se=QE(P)?{
    format:"AEP",data:await P.arrayBuffer()
  }:{
    format:"AEPX",xmlString:await P.text()
  },J=se.format.toLowerCase();
  try{
    if(m.importToAssetsOnly){
      const te=await YJ({
        toolkit:C,input:se,name:_,addSlotToThemes:fe=>{
          Yi(n,fe)
        },fontLoaderActor:z
      });
      te&&H.push(te.nodeId)
    }else await UJ({
      toolkit:C,input:se,activeScene:S.scene,onLayersSelect:G,onImportComplete:m.onImportComplete??void 0,selectedNodeId:Z,setTimelineForFpsChange:l,addSlotToThemes:te=>{
        Yi(n,te)
      },importPosition:$,wrapInPrecomposition:m.wrapInPrecomposition,fontLoaderActor:z
    });
    o+=1,at({
      system:n,data:{
        eventType:ce.AssetAdded,parameters:{
          source:m.source,type:J
        }
      }
    })
  }catch(te){
    Fr.notify(te,fe=>{
      fe.context=`${
        se.format
      } import failed`,fe.addMetadata("import",{
        fileName:_,source:m.source
      })
    }),r+=1
  }
}else if(kk(P)){
  const se=await P.text();
  let J;
  try{
    J=JSON.parse(se)
  }catch{
    r+=1;
    continue
  }if(!m.importToAssetsOnly&&!m.skipFeatureCheck)try{
    const{
      unsupportedFeatures:te,supportedFeatures:fe
    }=U0({
      json:J,jsonString:se,creatorHash:I
    });
    if(te.length){
      t({
        type:"contains-unsupported-features",unsupportedFeatures:te,supportedFeatures:fe
      });
      break
    }
  }catch{
    r+=1;
    continue
  }try{
    if(m.importToAssetsOnly){
      const te=await OJ({
        toolkit:C,json:J,name:_,addSlotToThemes:fe=>{
          Yi(n,fe)
        },fontLoaderActor:z
      });
      te&&H.push(te.nodeId)
    }else await Ax({
      toolkit:C,json:J,activeScene:S.scene,onLayersSelect:G,onImportComplete:m.onImportComplete??void 0,selectedNodeId:Z,setTimelineForFpsChange:l,addSlotToThemes:te=>{
        Yi(n,te)
      },importPosition:$,fontLoaderActor:z,wrapInPrecomposition:m.wrapInPrecomposition
    });
    o+=1,at({
      system:n,data:{
        eventType:ce.AssetAdded,parameters:{
          source:m.source,type:"lottie"
        }
      }
    })
  }catch{
    r+=1
  }
}else{
  const se=await P.arrayBuffer();
  if(!m.importToAssetsOnly&&!m.skipFeatureCheck)try{
    const J=await TJ(se),{
      unsupportedFeatures:te,supportedFeatures:fe
    }=U0({
      json:J,creatorHash:I
    });
    if(te.length){
      t({
        type:"contains-unsupported-features",unsupportedFeatures:te,supportedFeatures:fe
      });
      break
    }
  }catch{
    r+=1;
    continue
  }try{
    if(m.importToAssetsOnly){
      const J=await jJ({
        toolkit:C,dotLottie:se,name:_,addThemes:h,addSlotToThemes:te=>{
          Yi(n,te)
        },fontLoaderActor:z
      });
      J&&H.push(J.nodeId)
    }else{
      const J=m.forceCenter??(!m.wrapInPrecomposition||v);
      await kJ({
        toolkit:C,dotLottie:se,activeScene:S.scene,onLayersSelect:G,onImportComplete:m.onImportComplete??void 0,selectedNodeId:Z,setTimelineForFpsChange:l,resolveNewSceneConflictingSlots:u,addStateMachines:f,addThemes:h,addSlotToThemes:te=>{
          Yi(n,te)
        },importPosition:{
          center:J,position:M
        },wrapInPrecomposition:m.wrapInPrecomposition,fontLoaderActor:z
      })
    }o+=1,at({
      system:n,data:{
        eventType:ce.AssetAdded,parameters:{
          source:m.source,type:"lottie"
        }
      }
    })
  }catch(J){
    i=J instanceof Error?J.message:"Unknown error occurred",r+=1
  }
}
}if(H.length>0){
  const j=K(n,p.AssetManager),P=[...C.scenes.map(_=>_.scene.nodeId),...C.assets.map(_=>_.nodeId)];
  j.send({
    type:"ASSET_MANAGER.APPEND_ASSETS",assetIds:H,allAssetIds:P
  })
}if(m.importToAssetsOnly){
  const j=K(n,p.Notifications),P=m.files.length;
  r!==0&&(r===P?j.send({
    type:"ADD_TOAST",notification:{
      key:"import-failed",variant:"error",message:"Asset import failed. How about giving it another go?"
    }
  }):j.send({
    type:"ADD_TOAST",notification:{
      key:"import-failed",variant:"error",message:"Some assets couldn't be imported. Please check and try again."
    }
  })),j.send({
    type:"DISMISS_NOTIFICATION",key:"loading-asset"
  }),A()
}else s===m.files.length&&(m.timelinesForFpsChange.length?t({
  type:"open-fps-check"
}):A())
};
e(m=>{
  switch(m.type){
    case"init":s=0,g(m.payload);
    break;
    case"cancel-file-import":s+=1,s>m.payload.files.length-1?A():g(m.payload);
    break;
    case"continue":g(m.payload);
    break;
    case"keep-project-frame-rate":d(m.payload,!0),A();
    break;
    case"use-asset-frame-rate":d(m.payload,!1),A();
    break
  }
})
}),JJ=Ct({
  actions:{
    "reset-context":({
      context:e
    })=>{
      e.files=[],e.skipFeatureCheck=!1,e.unsupportedFeatures=[],e.supportedFeatures=[],e.timelinesForFpsChange=[],e.wrapInPrecomposition=!0,e.source=null,e.targetScene=null,e.forceCenter=null,e.onImportComplete=null,e.importToAssetsOnly=!1
    },"assign-files-to-context":Y(({
      context:e,event:t,system:n
    })=>(Me(t,["assign-files-to-context","START_IMPORT_FILES"]),K(n,p.Notifications).send({
      type:"ADD_BANNER",notification:{
        key:"loading-asset",variant:"loading",message:"Inserting asset..."
      }
    }),{
      files:t.files??e.files,mousePosition:t.mousePosition??e.mousePosition??null,wrapInPrecomposition:t.wrapInPrecomposition??e.wrapInPrecomposition,source:t.source??e.source,targetScene:t.targetScene??e.targetScene??null,forceCenter:t.forceCenter??e.forceCenter??null,onImportComplete:t.onImportComplete??e.onImportComplete??null,importToAssetsOnly:t.importToAssetsOnly??e.importToAssetsOnly??!1
    })),"skip-feature-check":Y({
      skipFeatureCheck:!0
    }),"notify-invalid-files-size":({
      context:e,system:t
    })=>{
      const n=K(t,p.Notifications),s=e.files.reduce((r,o)=>(G0(o)&&(r+=1),r),0);
      n.send({
        type:"ADD_BANNER",notification:{
          key:"file-size-error",variant:"error",message:`File${
            s>1?"s":""
          } cannot be larger than ${
            Mk
          }MB ${
            e.files.length>1?`(${
              s
            }/${
              e.files.length
            })`:""
          }`
        }
      }),n.send({
        type:"DISMISS_NOTIFICATION",key:"loading-asset"
      })
    },"notify-invalid-files-type":({
      context:e,system:t
    })=>{
      const n=K(t,p.Notifications),s=e.files.reduce((r,o)=>(PE(o)&&(r+=1),r),0);
      n.send({
        type:"ADD_BANNER",notification:{
          key:"file-type-error",variant:"error",message:s>1?`File formats are not supported (${
            s
          }/${
            e.files.length
          })`:"File format not supported"
        }
      }),n.send({
        type:"DISMISS_NOTIFICATION",key:"loading-asset"
      })
    },"notify-completion-status":({
      event:e,context:t,system:n
    })=>{
      Me(e,"complete");
      const s=K(n,p.Notifications);
      if(!(t.files.length===1&&e.importFailedFilesCount===0&&e.importSuccededFilesCount===0)){
        if(e.importFailedFilesCount===0){
          s.send({
            type:"DISMISS_NOTIFICATION",key:"loading-asset"
          });
          return
        }e.importFailedFilesCount===t.files.length?s.send({
          type:"ADD_TOAST",notification:{
            key:"import-failed",variant:"error",message:e.errorMessage??"Asset insert failed. Try again."
          }
        }):s.send({
          type:"ADD_TOAST",notification:{
            key:"import-failed",variant:"warning",message:e.errorMessage??"Some assets couldn't be inserted. Try again."
          }
        }),s.send({
          type:"DISMISS_NOTIFICATION",key:"loading-asset"
        })
      }
    },"notify-limited-support":({
      system:e
    })=>{
      const t=K(e,p.Notifications),n=K(e,p.WorkspaceMode);
      t.send({
        type:"ADD_BANNER",notification:{
          key:"limited-support",message:"Limited support: rendering or export may have issues.",cta:{
            label:"Safe mode",onClick:()=>{
              n.send({
                type:"SWITCH_THEMING_MODE"
              })
            }
          }
        }
      })
    },"set-features-to-context":Y(({
      event:e
    })=>(Me(e,"contains-unsupported-features"),{
      unsupportedFeatures:e.unsupportedFeatures,supportedFeatures:e.supportedFeatures
    })),"enable-safe-mode":Ie(({
      system:e
    })=>e.get("workspaceMode"),{
      type:"SWITCH_THEMING_MODE"
    }),"set-timeline-for-fps-change":Y(({
      event:e,context:t
    })=>(Me(e,"set-timeline-for-fps-change"),{
      timelinesForFpsChange:[...t.timelinesForFpsChange,e.payload]
    })),"track-feature-check-event":({
      context:e,system:t,event:n
    })=>{
      const s={
        cancel:Be.Cancel,"open-in-safe-mode":Be.SafeMode,"open-anyway":Be.Open
      };
      e.source&&s[n.type]&&at({
        system:t,data:{
          eventType:ce.FeatureCheck,parameters:{
            action:s[n.type],source:e.source,unsupported_count:e.unsupportedFeatures.length,unsupported_features:e.unsupportedFeatures,supported_count:e.supportedFeatures.length,supported_features:e.supportedFeatures
          }
        }
      })
    }
  },guards:{
    "are-files-valid-size":({
      context:e
    })=>!e.files.some(t=>G0(t)),"are-files-valid-type":({
      context:e
    })=>!e.files.some(t=>PE(t))
  },actors:{
    "import-files-to-creator-actor":KJ
  }
}).createMachine({
  context:{
    files:[],skipFeatureCheck:!1,unsupportedFeatures:[],supportedFeatures:[],timelinesForFpsChange:[],wrapInPrecomposition:!0,source:null,targetScene:null,forceCenter:null,onImportComplete:null,mousePosition:null,importToAssetsOnly:!1
  },initial:"idle",states:{
    idle:{
      entry:"reset-context",on:{
        START_IMPORT_FILES:{
          actions:["assign-files-to-context"],target:"validate-files"
        }
      }
    }
  }
});

// --- [FIX] File was truncated here. The remaining state machine states (validate-files, etc.) are missing from the extracted source. ---

