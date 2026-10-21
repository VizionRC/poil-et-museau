/* Poil & Museau — comportements communs à toutes les pages */
(function(){
  var root=document.documentElement;
  root.classList.add("js");
  try{var t=localStorage.getItem("pm-theme");if(t)root.dataset.theme=t;}catch(e){}

  /* Image introuvable ou bloquée : on garde la mise en page avec un repli */
  document.addEventListener("error",function(ev){
    var im=ev.target;if(!im||im.tagName!=="IMG")return;
    var p=im.parentElement;
    if(im.closest(".prose")){im.style.display="none";var fig=im.closest("div,p");if(fig&&!fig.textContent.trim())fig.style.display="none";return;}
    if(p&&(p.classList.contains("sp")||p.tagName==="A"&&p.parentElement&&p.parentElement.classList.contains("figure"))){im.style.display="none";return;}
    if(p){p.classList.add("img-off");if(p.classList.contains("figure"))p.style.display="none";}
  },true);

  document.addEventListener("DOMContentLoaded",function(){
    /* Thème */
    var tb=document.getElementById("theme");
    if(tb)tb.addEventListener("click",function(){
      var dark=root.dataset.theme?root.dataset.theme==="dark":matchMedia("(prefers-color-scheme: dark)").matches;
      root.dataset.theme=dark?"light":"dark";
      try{localStorage.setItem("pm-theme",root.dataset.theme);}catch(e){}
    });

    /* Menu mobile */
    var bg=document.getElementById("burger"),mm=document.getElementById("mm");
    if(bg&&mm)bg.addEventListener("click",function(){
      mm.hidden=!mm.hidden;bg.setAttribute("aria-expanded",String(!mm.hidden));
    });

    /* En-tête, progression, retour en haut */
    var hdr=document.querySelector("header.site"),top=document.getElementById("top"),prog=document.getElementById("progress");
    function onScroll(){
      var y=scrollY,h=document.documentElement.scrollHeight-innerHeight;
      if(hdr)hdr.classList.toggle("scrolled",y>20);
      if(top)top.classList.toggle("show",y>800);
      if(prog)prog.style.width=(h>0?y/h*100:0)+"%";
    }
    addEventListener("scroll",onScroll,{passive:true});onScroll();
    if(top)top.addEventListener("click",function(){scrollTo({top:0,behavior:"smooth"});});

    /* Apparition au défilement */
    var els=document.querySelectorAll(".reveal");
    if("IntersectionObserver" in window){
      var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add("in");io.unobserve(e.target);}});},{threshold:.08});
      els.forEach(function(el){io.observe(el);});
      setTimeout(function(){els.forEach(function(el){el.classList.add("in");});},2500);
    }else els.forEach(function(el){el.classList.add("in");});

    /* Compteurs */
    document.querySelectorAll("[data-count]").forEach(function(el){
      var end=+el.dataset.count,suf=el.dataset.suffix||"",s=null;
      function step(t){if(!s)s=t;var p=Math.min((t-s)/1400,1);el.textContent=Math.round(end*(1-Math.pow(1-p,3)))+suf;if(p<1)requestAnimationFrame(step);}
      requestAnimationFrame(step);
    });

    /* Mot changeant (accueil) */
    var sw=document.getElementById("swap");
    if(sw){var words=["chien","chat","museau","poil"],wi=0;
      setInterval(function(){wi=(wi+1)%words.length;sw.innerHTML="<span>"+words[wi]+"</span>";},2400);}

    /* Traces de pattes (accueil) */
    var hero=document.querySelector(".hero[data-paws]");
    if(hero&&!matchMedia("(prefers-reduced-motion: reduce)").matches){var last=0;
      hero.addEventListener("pointermove",function(e){
        var now=Date.now();if(now-last<120)return;last=now;
        var r=hero.getBoundingClientRect(),p=document.createElement("span");
        p.className="paw-trail";p.textContent="🐾";p.setAttribute("aria-hidden","true");
        p.style.left=(e.clientX-r.left-9)+"px";p.style.top=(e.clientY-r.top-9)+"px";
        hero.appendChild(p);setTimeout(function(){p.remove();},1200);
      });}

    /* Cartes à retourner */
    document.querySelectorAll(".flip").forEach(function(c){
      function t(e){if(e.target.tagName!=="A")c.classList.toggle("on");}
      c.addEventListener("click",t);c.addEventListener("keydown",function(e){if(e.key==="Enter"||e.key===" "){e.preventDefault();t(e);}});
    });

    /* Filtres de liste d'articles */
    var list=document.querySelector("[data-list]");
    if(list){
      var cards=[].slice.call(list.querySelectorAll(".card")),state={sp:"all",cat:"all",q:""};
      var empty=document.getElementById("empty"),cnt=document.getElementById("count");
      var norm=function(s){return s.normalize("NFD").replace(/[̀-ͯ]/g,"").toLowerCase();};
      function apply(){
        var q=norm(state.q),n=0;
        cards.forEach(function(c){
          var ok=(state.sp==="all"||c.dataset.sp===state.sp||c.dataset.sp==="both")&&(state.cat==="all"||c.dataset.cat===state.cat)&&(!q||norm(c.textContent).indexOf(q)>-1);
          c.hidden=!ok;if(ok)n++;
        });
        if(empty)empty.hidden=n>0;
        if(cnt)cnt.textContent=n+(n>1?" articles":" article");
      }
      var seg=document.getElementById("seg");
      function movePill(){if(!seg)return;var on=seg.querySelector("button.on"),p=seg.querySelector(".pill");if(on&&p){p.style.left=on.offsetLeft+"px";p.style.width=on.offsetWidth+"px";}}
      if(seg){seg.addEventListener("click",function(e){var b=e.target.closest("button");if(!b)return;state.sp=b.dataset.sp;seg.querySelectorAll("button").forEach(function(x){x.classList.toggle("on",x===b);x.setAttribute("aria-pressed",String(x===b));});movePill();apply();});
        addEventListener("resize",movePill);setTimeout(movePill,50);if(document.fonts)document.fonts.ready.then(movePill);}
      var chips=document.getElementById("chips");
      if(chips)chips.addEventListener("click",function(e){var b=e.target.closest(".chip");if(!b)return;state.cat=b.dataset.cat;chips.querySelectorAll(".chip").forEach(function(x){x.classList.toggle("on",x===b);x.setAttribute("aria-pressed",String(x===b));});apply();});
      var q=document.getElementById("q");
      if(q)q.addEventListener("input",function(){state.q=q.value;apply();});
      /* Catégorie présélectionnée par l'ancre (#sante, #comportement…) */
      var h=location.hash.replace("#","");
      if(h&&chips){var pre=chips.querySelector('[data-cat="'+h+'"]');if(pre)pre.click();}
      apply();
    }

    /* Outil aliments */
    var foods=document.getElementById("foods"),ver=document.getElementById("verdict");
    if(foods&&ver&&window.PM_FOODS){
      var F=window.PM_FOODS,base=foods.dataset.base||"";
      foods.addEventListener("click",function(e){
        var b=e.target.closest(".food");if(!b)return;
        foods.querySelectorAll(".food").forEach(function(x){x.classList.toggle("on",x===b);x.setAttribute("aria-pressed",String(x===b));});
        var x=F[+b.dataset.i],ico=x.l==="bad"?"⛔ ":x.l==="ok"?"✅ ":"⚠️ ";
        var help=x.l==="bad"
          ?'Votre animal en a mangé? Appelez rapidement votre vétérinaire ou une clinique d’urgence. <a href="'+base+'articles/que-faire-si-mon-chien-ou-mon-chat-mange-un-aliment-dangereux.html">Que faire →</a>'
          :'Toujours en petite quantité et en complément de son alimentation habituelle. <a href="'+base+'articles/aliments-dangereux-chien-chat.html">Voir les 10 aliments à éviter →</a>';
        ver.innerHTML='<div class="big" aria-hidden="true">'+x.e+'</div><span class="badge '+x.l+'">'+ico+x.v+'</span><h3>'+x.n+'</h3><p>'+x.d+'</p><small>'+help+'</small>';
        ver.classList.remove("bump");void ver.offsetWidth;ver.classList.add("bump");
      });
    }

    /* Table des matières active (article) */
    var tocLinks=document.querySelectorAll(".toc a[href^='#']");
    if(tocLinks.length&&"IntersectionObserver" in window){
      var map={};tocLinks.forEach(function(a){map[a.getAttribute("href").slice(1)]=a;});
      var tio=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){tocLinks.forEach(function(a){a.classList.remove("on");});var a=map[e.target.id];if(a)a.classList.add("on");}});},{rootMargin:"-20% 0px -70% 0px"});
      Object.keys(map).forEach(function(id){var h=document.getElementById(id);if(h)tio.observe(h);});
    }

    /* Copier le lien / l'adresse */
    document.querySelectorAll("[data-copy]").forEach(function(b){
      b.addEventListener("click",function(){
        var txt=b.dataset.copy==="url"?location.href:b.dataset.copy,orig=b.textContent;
        function done(){b.textContent="Copié ✓";setTimeout(function(){b.textContent=orig;},1800);}
        function fallback(){var s=b.parentNode.querySelector("span");if(s){var r=document.createRange();r.selectNodeContents(s);var sel=getSelection();sel.removeAllRanges();sel.addRange(r);}}
        if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(txt).then(done,fallback);}else fallback();
      });
    });

    /* Formulaires (démo : aucun envoi réel pour l'instant) */
    document.querySelectorAll("form[data-demo]").forEach(function(f){
      f.addEventListener("submit",function(e){
        e.preventDefault();var m=f.querySelector("[data-ok]");if(m)m.hidden=false;
        f.querySelectorAll("input,textarea").forEach(function(i){if(i.type!=="checkbox")i.value="";});
      });
    });

    var yr=document.getElementById("yr");if(yr)yr.textContent=new Date().getFullYear();
  });
})();
