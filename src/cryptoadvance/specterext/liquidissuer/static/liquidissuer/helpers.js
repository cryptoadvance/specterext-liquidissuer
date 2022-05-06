// common helper functions and global listeners

// Enable navigation loader
window.addEventListener('beforeunload', function (e) {
	// half a second delay before we show it
	window.setTimeout(()=>{
		document.getElementById("pageloader").style.display = 'block';
	}, 200);
});

// Disable all submit buttons after form submit
window.addEventListener('load', ()=>{
    Array.from(document.querySelectorAll("form")).forEach(form => {
        form.addEventListener('submit', ()=>{
            window.setTimeout(()=>{
                Array.from(form.querySelectorAll('button[type=submit]')).forEach((btn)=>{
                    btn.disabled = true;
                });
            }, 100);
            return true;
        })
    });
})