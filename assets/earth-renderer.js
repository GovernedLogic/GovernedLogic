/* Native ray/sphere Earth renderer. Texture inputs are surface materials, never a composed scene. */
window.GLCreateEarth = function(onReady) {
  'use strict';
  const canvas=document.createElement('canvas');
  const gl=canvas.getContext('webgl',{alpha:true,premultipliedAlpha:false,antialias:false,preserveDrawingBuffer:true});
  if(!gl)return null;
  const vertex='attribute vec2 p;void main(){gl_Position=vec4(p,0.,1.);}';
  const fragment=`precision highp float;
    uniform vec2 resolution,center;uniform float radius,cap,scale;
    uniform sampler2D dayMap,nightMap,cloudMap;
    const float PI=3.14159265359;
    void main(){
      vec2 pixel=vec2(gl_FragCoord.x,resolution.y-gl_FragCoord.y);
      vec2 q=(pixel-center)/radius; q.y=-q.y;
      float rr=dot(q,q);float edge=sqrt(rr);
      float depth=(pixel.y-(center.y-radius))/max(.01,scale);
      float capFade=mix(1.,1.-smoothstep(28.,148.,depth),cap);
      float sideFade=mix(1.,exp(-pow(abs(pixel.x-center.x)/(465.*scale),4.)),cap);
      float fade=capFade*sideFade;
      if(fade<.002){gl_FragColor=vec4(0.);return;}
      if(rr>1.){
        float halo=exp(-(edge-1.)*radius/(3.2*scale));
        float a=halo*.42*fade;
        gl_FragColor=vec4(.09,.42,.85,a);return;
      }
      vec3 n=vec3(q,sqrt(1.-rr));
      // Rotate geography on the sphere; the radius remains equal in both axes.
      float angle=mix(.05,1.02,cap);vec3 r=n;
      r.y=n.y*cos(angle)-n.z*sin(angle);r.z=n.y*sin(angle)+n.z*cos(angle);
      vec2 uv=vec2(atan(r.z,r.x)/(2.*PI)+.52,asin(r.y)/PI+.5);
      vec3 tex=texture2D(dayMap,uv).rgb;
      vec3 night=texture2D(nightMap,uv).rgb;
      vec4 cloud=texture2D(cloudMap,uv+vec2(.003,0.));
      vec3 light=normalize(vec3(-.25,.83,.40));
      float diffuse=max(dot(n,light),0.);
      float fresnel=pow(1.-n.z,4.);
      float landLight=mix(.15+.84*diffuse,.11+.64*diffuse,cap);
      vec3 surface=pow(tex,vec3(1.15))*landLight;
      float c=cloud.r*.55;
      surface=mix(surface,vec3(.72,.80,.85)*(.2+.7*diffuse),c);
      float darkness=1.-smoothstep(.1,.55,diffuse);
      surface+=night*vec3(1.0,.73,.42)*darkness*.9;
      surface+=vec3(.035,.20,.40)*fresnel*.68;
      float aa=1.-smoothstep(1.-1.2/radius,1.,edge);
      gl_FragColor=vec4(surface,fade*aa);
    }`;
  function shader(type,source){const s=gl.createShader(type);gl.shaderSource(s,source);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));return s;}
  let program;
  try{program=gl.createProgram();gl.attachShader(program,shader(gl.VERTEX_SHADER,vertex));gl.attachShader(program,shader(gl.FRAGMENT_SHADER,fragment));gl.linkProgram(program);if(!gl.getProgramParameter(program,gl.LINK_STATUS))return null;}catch{return null;}
  gl.useProgram(program);const buffer=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,buffer);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,-1,1,1,-1,1,1]),gl.STATIC_DRAW);
  const p=gl.getAttribLocation(program,'p');gl.enableVertexAttribArray(p);gl.vertexAttribPointer(p,2,gl.FLOAT,false,0,0);
  const uniforms={};for(const k of ['resolution','center','radius','cap','scale'])uniforms[k]=gl.getUniformLocation(program,k);
  let loaded=0;
  for(const [i,key,url] of [[0,'dayMap','assets/materials/earth-day.jpg'],[1,'nightMap','assets/materials/earth-night.jpg'],[2,'cloudMap','assets/materials/earth-clouds.jpg']]){
    const texture=gl.createTexture();gl.activeTexture(gl.TEXTURE0+i);gl.bindTexture(gl.TEXTURE_2D,texture);
    gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,1,1,0,gl.RGBA,gl.UNSIGNED_BYTE,new Uint8Array(i===0?[18,52,77,255]:[0,0,0,255]));
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);
    gl.uniform1i(gl.getUniformLocation(program,key),i);
    const image=new Image();image.onload=()=>{gl.activeTexture(gl.TEXTURE0+i);gl.bindTexture(gl.TEXTURE_2D,texture);gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL,true);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,image);loaded++;if(loaded===3)onReady?.();};image.src=url;
  }
  return {canvas,render(w,h,dpr,x,y,r,cap,s){
    const W=Math.round(w*dpr),H=Math.round(h*dpr);
    if(canvas.width!==W||canvas.height!==H){canvas.width=W;canvas.height=H;gl.viewport(0,0,W,H);}
    gl.useProgram(program);gl.uniform2f(uniforms.resolution,W,H);gl.uniform2f(uniforms.center,x*dpr,y*dpr);gl.uniform1f(uniforms.radius,r*dpr);gl.uniform1f(uniforms.cap,cap);gl.uniform1f(uniforms.scale,Math.max(.01,s)*dpr);gl.clearColor(0,0,0,0);gl.clear(gl.COLOR_BUFFER_BIT);gl.drawArrays(gl.TRIANGLES,0,6);return canvas;
  }};
};
