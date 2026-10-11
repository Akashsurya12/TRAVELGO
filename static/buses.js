const buses = [
  {
    id: "BUS_01",
    _id: "BUS_01",
    source: "Hyderabad",
    destination: "Bangalore",
    name: "Rajdhani Express",
    type: "AC Sleeper",
    time: "7:00 PM",
    price: 850
  },
  {
    id: "BUS_02",
    _id: "BUS_02",
    source: "Hyderabad",
    destination: "Bangalore",
    name: "VRL Travels",
    type: "Non-AC Sleeper",
    time: "8:30 PM",
    price: 620
  },
  {
    id: "BUS_03",
    _id: "BUS_03",
    source: "Hyderabad",
    destination: "Bangalore",
    name: "Orange Travels",
    type: "AC Semi-Sleeper",
    time: "6:15 PM",
    price: 780
  },
  {
    id: "BUS_04",
    _id: "BUS_04",
    source: "Hyderabad",
    destination: "Bangalore",
    name: "Kaveri Travels",
    type: "Sleeper",
    time: "9:00 PM",
    price: 700
  },
  {
    id: "BUS_05",
    _id: "BUS_05",
    source: "Hyderabad",
    destination: "Bangalore",
    name: "TSRTC",
    type: "AC Sleeper",
    time: "10:00 PM",
    price: 900
  },
  {
    id: "BUS_06",
    _id: "BUS_06",
    source: "Hyderabad",
    destination: "Bangalore",
    name: "SRS Travels",
    type: "Non-AC Sleeper",
    time: "5:30 PM",
    price: 610
  },
  {
    id: "BUS_07",
    _id: "BUS_07",
    source: "Bangalore",
    destination: "Chennai",
    name: "SRS Travels",
    type: "AC Semi-Sleeper",
    time: "6:00 PM",
    price: 700
  },
  {
    id: "BUS_08",
    _id: "BUS_08",
    source: "Bangalore",
    destination: "Chennai",
    name: "KPN Travels",
    type: "Non-AC Sleeper",
    time: "9:00 PM",
    price: 580
  },
  {
    id: "BUS_09",
    _id: "BUS_09",
    source: "Bangalore",
    destination: "Chennai",
    name: "GreenLine",
    type: "Sleeper",
    time: "8:00 PM",
    price: 640
  },
  {
    id: "BUS_10",
    _id: "BUS_10",
    source: "Bangalore",
    destination: "Chennai",
    name: "TSRTC",
    type: "AC Sleeper",
    time: "7:45 PM",
    price: 750
  },
  {
    id: "BUS_11",
    _id: "BUS_11",
    source: "Bangalore",
    destination: "Chennai",
    name: "Orange Travels",
    type: "Non-AC Sleeper",
    time: "9:15 PM",
    price: 600
  },
  {
    id: "BUS_12",
    _id: "BUS_12",
    source: "Bangalore",
    destination: "Chennai",
    name: "Raj Express",
    type: "AC Semi-Sleeper",
    time: "6:30 PM",
    price: 720
  },
  {
    id: "BUS_13",
    _id: "BUS_13",
    source: "Chennai",
    destination: "Hyderabad",
    name: "TSRTC",
    type: "AC Sleeper",
    time: "10:00 PM",
    price: 810
  },
  {
    id: "BUS_14",
    _id: "BUS_14",
    source: "Chennai",
    destination: "Hyderabad",
    name: "GreenLine",
    type: "AC Semi-Sleeper",
    time: "5:00 PM",
    price: 760
  },
  {
    id: "BUS_15",
    _id: "BUS_15",
    source: "Chennai",
    destination: "Hyderabad",
    name: "KPN Travels",
    type: "Sleeper",
    time: "8:30 PM",
    price: 700
  },
  {
    id: "BUS_16",
    _id: "BUS_16",
    source: "Chennai",
    destination: "Hyderabad",
    name: "Orange Travels",
    type: "Non-AC Sleeper",
    time: "9:45 PM",
    price: 680
  },
  {
    id: "BUS_17",
    _id: "BUS_17",
    source: "Chennai",
    destination: "Hyderabad",
    name: "VRL",
    type: "AC Sleeper",
    time: "6:00 PM",
    price: 790
  },
  {
    id: "BUS_18",
    _id: "BUS_18",
    source: "Chennai",
    destination: "Hyderabad",
    name: "Raj Express",
    type: "AC Semi-Sleeper",
    time: "7:30 PM",
    price: 740
  },
  {
    id: "BUS_19",
    _id: "BUS_19",
    source: "Hyderabad",
    destination: "Chennai",
    name: "Orange Travels",
    type: "Non-AC Sleeper",
    time: "6:45 PM",
    price: 630
  },
  {
    id: "BUS_20",
    _id: "BUS_20",
    source: "Hyderabad",
    destination: "Chennai",
    name: "KKR Travels",
    type: "AC Sleeper",
    time: "9:30 PM",
    price: 820
  },
  {
    id: "BUS_21",
    _id: "BUS_21",
    source: "Hyderabad",
    destination: "Chennai",
    name: "SRS Travels",
    type: "Sleeper",
    time: "10:15 PM",
    price: 700
  },
  {
    id: "BUS_22",
    _id: "BUS_22",
    source: "Hyderabad",
    destination: "Chennai",
    name: "TSRTC",
    type: "AC Semi-Sleeper",
    time: "5:30 PM",
    price: 780
  },
  {
    id: "BUS_23",
    _id: "BUS_23",
    source: "Hyderabad",
    destination: "Chennai",
    name: "VRL",
    type: "Non-AC Sleeper",
    time: "8:00 PM",
    price: 650
  },
  {
    id: "BUS_24",
    _id: "BUS_24",
    source: "Hyderabad",
    destination: "Chennai",
    name: "Raj Express",
    type: "AC Sleeper",
    time: "9:00 PM",
    price: 830
  },
  {
    id: "BUS_25",
    _id: "BUS_25",
    source: "Bangalore",
    destination: "Hyderabad",
    name: "Sri Balaji",
    type: "AC Sleeper",
    time: "11:00 PM",
    price: 870
  },
  {
    id: "BUS_26",
    _id: "BUS_26",
    source: "Bangalore",
    destination: "Hyderabad",
    name: "Kaveri Travels",
    type: "Non-AC Sleeper",
    time: "8:00 PM",
    price: 590
  },
  {
    id: "BUS_27",
    _id: "BUS_27",
    source: "Bangalore",
    destination: "Hyderabad",
    name: "TSRTC",
    type: "Sleeper",
    time: "10:30 PM",
    price: 710
  },
  {
    id: "BUS_28",
    _id: "BUS_28",
    source: "Bangalore",
    destination: "Hyderabad",
    name: "GreenLine",
    type: "AC Semi-Sleeper",
    time: "7:15 PM",
    price: 765
  },
  {
    id: "BUS_29",
    _id: "BUS_29",
    source: "Bangalore",
    destination: "Hyderabad",
    name: "Orange Travels",
    type: "AC Sleeper",
    time: "6:00 PM",
    price: 880
  },
  {
    id: "BUS_30",
    _id: "BUS_30",
    source: "Bangalore",
    destination: "Hyderabad",
    name: "KKR Travels",
    type: "Non-AC Sleeper",
    time: "9:45 PM",
    price: 620
  }
];
