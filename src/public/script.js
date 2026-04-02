const func = document.getElementById("func")
const out = document.getElementById("out")
const modWeight = document.getElementById("modWeight")
const callWeight = document.getElementById("callWeight")

let timeout = 0

async function handleInput() {
	const names = func.value.trim()
	if (!names) return out.innertText = ""
	const input = { 
		names,
		modWeight: modWeight.value,
		callWeight: callWeight.value,
	}
	const params = new URLSearchParams(input)

	const data = await fetch("/api/query.json?" + params.toString()).then(r => r.json()).catch(console.error);
	

	if (!data?.devs) {
		console.error(data)
		out.innerText = "Error"
		return
	}

	if (!data.devs.length) {
		out.innerText = "No match devs"
		return
	}

	out.innerText = ""

	data.devs.forEach((d, i) => {
		const p = document.createElement("p");
		p.innerText = `#${i + 1} ${d.github?.login || (d.id + " (Missing name map)")} (Score: ${d.score.toFixed(2)})`
		p.appendChild(document.createElement("br"))
		d.methods.forEach(m => {
			p.append(`${m.name}: commits=${m.commits}, modifications=${m.modifications.toFixed(2)}, calls=${m.calls.toFixed(2)}`)
			p.appendChild(document.createElement("br"))
		})
		out.appendChild(p);
	})
}

function onInput() {
	clearTimeout(timeout)
	timeout = setTimeout(handleInput, 200)
}
func.addEventListener("input", onInput);
modWeight.addEventListener("input", onInput);
callWeight.addEventListener("input", onInput);

console.log(func)
