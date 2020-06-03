//Cliques sur Menu, apparition de celui-ci
var btn=document.querySelector('.toggle_btn');
var nav=document.querySelector('.nav');
btn.onclick=function(){
	btn.classList.toggle('toggle_btn'); //suppression de la classe toggle_btn
	btn.classList.toggle('toggle_btn_hidden'); //ajout de la classe toggle_btn_hidden
	nav.classList.toggle('nav'); //suppression de la classe nav
	nav.classList.toggle('nav_open'); //ajout de la classe nav_open
}

//Cliques sur la croix, disparition du menu
var btn_exit=document.querySelector('.fa-times');
btn_exit.onclick=function(){
	btn.classList.toggle('toggle_btn');
	btn.classList.toggle('toggle_btn_hidden');
	nav.classList.toggle('nav');
	nav.classList.toggle('nav_open');
}

