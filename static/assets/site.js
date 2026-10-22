/* Poil & Museau — comportements communs à toutes les pages */
(function(){
  var root=document.documentElement;
  /* Animations décoratives en continu : lancées à la première interaction seulement */
  function live(){root.classList.add("live");["pointerdown","keydown","touchstart","wheel","mousemove"].forEach(function(ev){removeEventListener(ev,live);});}
  ["pointerdown","keydown","touchstart","wheel","mousemove"].forEach(function(ev){addEventListener(ev,live,{passive:true,once:true});});


  /* Google Analytics : chargé seulement après consentement explicite (Loi 25) */
  var CK="pm-consent";
  function getC(){try{return localStorage.getItem(CK);}catch(e){return null;}}
  function setC(v){try{localStorage.setItem(CK,v);}catch(e){}}
  function loadGA(id){
    if(!id||window.__pmGA)return;window.__pmGA=1;
    window.dataLayer=window.dataLayer||[];window.gtag=function(){dataLayer.push(arguments);};
    gtag("js",new Date());gtag("config",id,{anonymize_ip:true});
    var s=document.createElement("script");s.async=true;s.src="https://www.googletagmanager.com/gtag/js?id="+encodeURIComponent(id);document.head.appendChild(s);
  }
  function clearGA(){
    document.cookie.split(";").forEach(function(c){var n=c.split("=")[0].trim();if(/^_ga/.test(n)){["",location.hostname,"."+location.hostname.replace(/^www\./,"")].forEach(function(d){document.cookie=n+"=; Max-Age=0; path=/"+(d?"; domain="+d:"");});}});
  }
  function banner(b){
    var old=document.getElementById("consent");if(old)old.remove();
    var d=b.dataset,el=document.createElement("div");
    el.id="consent";el.className="consent";el.setAttribute("role","region");el.setAttribute("aria-label",d.consentLabel||"Cookies");
    el.innerHTML='<p></p><div class="consent-btns"><button type="button" class="btn btn-ghost" data-v="no"></button><button type="button" class="btn btn-primary" data-v="yes"></button></div>';
    var p=el.querySelector("p");p.textContent=d.consentText+" ";
    var a=document.createElement("a");a.href=d.consentHref;a.textContent=d.consentMore;p.appendChild(a);
    el.querySelector('[data-v="yes"]').textContent=d.consentYes;el.querySelector('[data-v="no"]').textContent=d.consentNo;
    el.addEventListener("click",function(ev){var v=ev.target.getAttribute&&ev.target.getAttribute("data-v");if(!v)return;
      setC(v);el.remove();if(v==="yes")loadGA(d.ga);else{clearGA();if(window.__pmGA)location.reload();}});
    document.body.appendChild(el);
  }
  document.addEventListener("DOMContentLoaded",function(){
    var b=document.body;if(!b||!b.dataset.ga)return;
    var c=getC();if(c==="yes")loadGA(b.dataset.ga);else if(c!=="no")banner(b);
    document.querySelectorAll("[data-consent-open]").forEach(function(x){x.addEventListener("click",function(){banner(b);});});
  });

  /* Clics vers Amazon : événement Google Analytics (si consentement) */
  document.addEventListener("click",function(ev){
    var a=ev.target.closest&&ev.target.closest('a[href*="amzn.to"],a[href*="link.amazon"],a[href*="amazon."]');
    if(!a||typeof window.gtag!=="function")return;
    gtag("event","clic_amazon",{link_url:a.href,link_text:(a.textContent||"").trim().slice(0,100),
      emplacement:a.closest(".amz-box")?"encadre_produits":a.classList.contains("amz-cta")?"bouton":"texte",transport_type:"beacon"});
  },true);

  /* Partage natif (téléphone) */
  document.addEventListener("DOMContentLoaded",function(){
    if(!navigator.share)return;
    document.querySelectorAll("[data-share]").forEach(function(btn){
      btn.hidden=false;
      btn.addEventListener("click",function(){navigator.share({title:btn.dataset.title||document.title,url:location.href}).catch(function(){});
        if(typeof window.gtag==="function")gtag("event","share",{method:"natif"});});
    });
  });
  document.addEventListener("click",function(ev){
    var a=ev.target.closest&&ev.target.closest(".share-bar a.sh");
    if(a&&typeof window.gtag==="function")gtag("event","share",{method:a.textContent.trim(),transport_type:"beacon"});
  },true);

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
    addEventListener("scroll",onScroll,{passive:true});requestAnimationFrame(onScroll);
    if(top)top.addEventListener("click",function(){scrollTo({top:0,behavior:"smooth"});});

    /* Apparition au défilement */
    var els=document.querySelectorAll(".reveal");
    if("IntersectionObserver" in window){
      var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add("in");io.unobserve(e.target);}});},{threshold:.08});
      /* Ce qui est déjà à l'écran reste visible dès le premier affichage */
      var vh=innerHeight;
      els.forEach(function(el){if(el.getBoundingClientRect().top<vh)el.classList.add("in");else io.observe(el);});
      root.classList.add("js-reveal");
      setTimeout(function(){els.forEach(function(el){if(!el.classList.contains("in")){el.style.transition="none";el.classList.add("in");}});},2500);
    }else els.forEach(function(el){el.classList.add("in");});

    /* Compteurs */
    document.querySelectorAll("[data-count]").forEach(function(el){
      var end=+el.dataset.count,suf=el.dataset.suffix||"",s=null;
      function step(t){if(!s)s=t;var p=Math.min((t-s)/1400,1);el.textContent=Math.round(end*(1-Math.pow(1-p,3)))+suf;if(p<1)requestAnimationFrame(step);}
      requestAnimationFrame(step);
    });

    /* Mot changeant (accueil) */
    var sw=document.getElementById("swap");
    if(sw){var words=(sw.dataset.words||"chien,chat,museau,poil").split(","),wi=0;
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
      if(q){q.addEventListener("input",function(){state.q=q.value;apply();});
        try{var qp=new URLSearchParams(location.search).get("q");if(qp){q.value=qp;state.q=qp;}}catch(e){}}
      /* Catégorie présélectionnée par l'ancre (#sante, #comportement…) */
      var h=location.hash.replace("#","");
      if(h&&chips){var pre=chips.querySelector('[data-cat="'+h+'"]');if(pre)pre.click();}
      apply();
    }

    /* Outil aliments */
    var foods=document.getElementById("foods"),ver=document.getElementById("verdict");
    if(foods&&ver&&window.PM_FOODS){
      var F=window.PM_FOODS,T=window.PM_TXT||{};
      foods.addEventListener("click",function(e){
        var b=e.target.closest(".food");if(!b)return;
        foods.querySelectorAll(".food").forEach(function(x){x.classList.toggle("on",x===b);x.setAttribute("aria-pressed",String(x===b));});
        var x=F[+b.dataset.i],ico=x.l==="bad"?"⛔ ":x.l==="ok"?"✅ ":"⚠️ ";
        var help=x.l==="bad"?T.bad+' <a href="'+T.badLink+'">'+T.badCta+'</a>':T.ok+' <a href="'+T.okLink+'">'+T.okCta+'</a>';
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
        function done(){b.textContent=document.body.dataset.copied||"Copié ✓";setTimeout(function(){b.textContent=orig;},1800);}
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
