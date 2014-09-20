// From http://mkweb.bcgsc.ca/circos/guide/tables/
 var chord = d3.layout.chord()
   .padding(.05)
   .sortSubgroups(d3.descending)
   .matrix([
        [358.0,269.0,185.0,154.0,157.0,103.0,119.0,89.0,87.0,67.0],
        [269.0,252.0,186.0,138.0,131.0,111.0,88.0,78.0,69.0,72.0],
        [185.0,186.0,168.0,89.0,95.0,77.0,59.0,56.0,36.0,64.0],
        [154.0,138.0,89.0,78.0,71.0,52.0,75.0,39.0,53.0,31.0],
        [157.0,131.0,95.0,71.0,60.0,49.0,53.0,48.0,51.0,41.0],
        [103.0,111.0,77.0,52.0,49.0,48.0,41.0,36.0,47.0,48.0],
        [119.0,88.0,59.0,75.0,53.0,41.0,52.0,25.0,32.0,20.0],
        [89.0,78.0,56.0,39.0,48.0,36.0,25.0,12.0,27.0,28.0],
        [87.0,69.0,36.0,53.0,51.0,47.0,32.0,27.0,34.0,32.0],
        [67.0,72.0,64.0,31.0,41.0,48.0,20.0,28.0,32.0,92.0]
    ]);
   
//      [11975,  5871, 8916, 2868],
//      [ 1951, 10048, 2060, 6171],
//      [ 8010, 16145, 8090, 8045],
//      [ 1013,   990,  940, 6907]
 
 var w = 700,
     h = 700,
     r0 = Math.min(w, h) * .41,
     r1 = r0 * 1.1;
 
 var fill = d3.scale.ordinal()
     .domain(d3.range(10))
     .range(["#000000", "#FFDD89", "#957244", "#F26223","00CC00","00FFFF","FF9933","0066FF","CC0099","FF0000"]);
 
 var svg = d3.select("#chart")
   .append("svg:svg")
     .attr("width", w)
     .attr("height", h)
   .append("svg:g")
     .attr("transform", "translate(" + w / 2 + "," + h / 2 + ")");
 
 svg.append("svg:g")
   .selectAll("path")
     .data(chord.groups)
   .enter().append("svg:path")
     .style("fill", function(d) { return fill(d.index); })
     .style("stroke", function(d) { return fill(d.index); })
     .attr("d", d3.svg.arc().innerRadius(r0).outerRadius(r1))
     .on("mouseover", fade(.1))
     .on("mouseout", fade(1));
 
 var ticks = svg.append("svg:g")
   .selectAll("g")
     .data(chord.groups)
   .enter().append("svg:g")
   .selectAll("g")
     .data(groupTicks)
   .enter().append("svg:g")
     .attr("transform", function(d) {
       return "rotate(" + (d.angle * 180 / Math.PI - 90) + ")"
           + "translate(" + r1 + ",0)";
     });
 
 ticks.append("svg:line")
     .attr("x1", 1)
     .attr("y1", 0)
     .attr("x2", 5)
     .attr("y2", 0)
     .style("stroke", "#000");
 
 ticks.append("svg:text")
     .attr("x", 8)
     .attr("dy", ".35em")
     .attr("text-anchor", function(d) {
       return d.angle > Math.PI ? "end" : null;
     })
     .attr("transform", function(d) {
       return d.angle > Math.PI ? "rotate(180)translate(-16)" : null;
     })
     .text(function(d) { return d.label; });
 
 svg.append("svg:g")
     .attr("class", "chord")
   .selectAll("path")
     .data(chord.chords)
   .enter().append("svg:path")
     .style("fill", function(d) { return fill(d.target.index); })
     .attr("d", d3.svg.chord().radius(r0))
     .style("opacity", 1);
     

 
 /** Returns an array of tick angles and labels, given a group. */
 function groupTicks(d) {
   var k = (d.endAngle - d.startAngle) / d.value;
   return d3.range(0, d.value, 100).map(function(v, i) {
     return {
       angle: v * k + d.startAngle,
       label: i % 1 ? null : v
     };
   });
 }
 
 /** Returns an event handler for fading a given chord group. */
 function fade(opacity) {
   return function(g, i) {
     svg.selectAll("g.chord path")
         .filter(function(d) {
           return d.source.index != i && d.target.index != i;
         })
       .transition()
         .style("opacity", opacity);
   };
 }