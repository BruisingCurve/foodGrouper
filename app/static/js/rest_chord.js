// From http://mkweb.bcgsc.ca/circos/guide/tables/
 var chord = d3.layout.chord()
   .padding(.05)
   .sortSubgroups(d3.descending)
   .matrix([
      [0.22544080604534006,0.16939546599496222,0.11649874055415617,0.09697732997481108,0.09886649874055416,0.06486146095717885,0.07493702770780857,0.05604534005037783,0.05478589420654912,0.04219143576826197],
      [0.19296987087517933,0.18077474892395984,0.133428981348637,0.09899569583931134,0.09397417503586801,0.07962697274031563,0.06312769010043041,0.05595408895265423,0.04949784791965567,0.05164992826398852],
      [0.18226600985221675,0.1832512315270936,0.16551724137931034,0.08768472906403942,0.09359605911330049,0.07586206896551724,0.05812807881773399,0.05517241379310345,0.035467980295566505,0.06305418719211822],
      [0.19743589743589743,0.17692307692307693,0.1141025641025641,0.1,0.09102564102564102,0.06666666666666667,0.09615384615384616,0.05,0.06794871794871794,0.03974358974358974],
      [0.20767195767195767,0.17328042328042328,0.12566137566137567,0.09391534391534391,0.07936507936507936,0.06481481481481481,0.0701058201058201,0.06349206349206349,0.06746031746031746,0.05423280423280423],
      [0.16830065359477125,0.18137254901960784,0.12581699346405228,0.08496732026143791,0.08006535947712418,0.0784313725490196,0.06699346405228758,0.058823529411764705,0.07679738562091504,0.0784313725490196],
      [0.21099290780141844,0.15602836879432624,0.10460992907801418,0.13297872340425532,0.09397163120567376,0.0726950354609929,0.09219858156028368,0.044326241134751775,0.05673758865248227,0.03546099290780142],
      [0.20319634703196346,0.1780821917808219,0.1278538812785388,0.08904109589041095,0.1095890410958904,0.0821917808219178,0.05707762557077625,0.0273972602739726,0.06164383561643835,0.0639269406392694],
      [0.1858974358974359,0.14743589743589744,0.07692307692307693,0.11324786324786325,0.10897435897435898,0.10042735042735043,0.06837606837606838,0.057692307692307696,0.07264957264957266,0.06837606837606838],
      [0.13535353535353536,0.14545454545454545,0.1292929292929293,0.06262626262626263,0.08282828282828283,0.09696969696969697,0.04040404040404041,0.05656565656565657,0.06464646464646465,0.18585858585858586]
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