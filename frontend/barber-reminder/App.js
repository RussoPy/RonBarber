import React, { useEffect, useState } from 'react';
import {
  View, Text, FlatList, Alert, TouchableOpacity,
  TextInput, Platform, StyleSheet, Linking
} from 'react-native';
import * as Contacts from 'expo-contacts';
import DateTimePicker from '@react-native-community/datetimepicker';
import { ref, onValue, set, remove, update } from 'firebase/database';
import { database } from './firebaseConfig';
import uuid from 'react-native-uuid';

const StyledButton = ({ title, onPress, color = '#5B2C6F' }) => (
  <TouchableOpacity onPress={onPress} style={[buttonStyles.button, { backgroundColor: color }]}>
    <Text style={buttonStyles.text}>{title}</Text>
  </TouchableOpacity>
);

export default function App() {
  const [contacts, setContacts] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [appointments, setAppointments] = useState([]);
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [showContacts, setShowContacts] = useState(false);
  const [showTimePicker, setShowTimePicker] = useState(false);
  const [contactToSchedule, setContactToSchedule] = useState(null);
  const [appointmentTime, setAppointmentTime] = useState(new Date());
  const [editingAppointmentId, setEditingAppointmentId] = useState(null);

  const dateKey = selectedDate.toISOString().split('T')[0];

  useEffect(() => {
    const dbRef = ref(database, `appointments/${dateKey}`);
    const unsubscribe = onValue(dbRef, (snapshot) => {
      const data = snapshot.val() || {};
      const list = Object.entries(data).map(([id, val]) => ({ id, ...val }));
      const sortedList = list.sort((a, b) => a.time.localeCompare(b.time));
      setAppointments(sortedList);
    });
    return () => unsubscribe();
  }, [selectedDate]);

  const loadContacts = async () => {
    if (Platform.OS === 'web') {
      alert("Contact access not supported on web.");
      return;
    }

    const { status } = await Contacts.requestPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert("Permission denied", "Enable contacts permission.");
      return;
    }

    const { data } = await Contacts.getContactsAsync({
      fields: [Contacts.Fields.PhoneNumbers],
    });

    const filtered = data.filter(c => c.phoneNumbers?.length > 0);
    setContacts(filtered);
    setShowContacts(true);
  };

  const handleContactPress = (contact) => {
    setContactToSchedule(contact);
    setShowTimePicker(true);
  };

  const confirmTimeAndSave = () => {
    const id = uuid.v4();
    const cleanPhone = contactToSchedule.phoneNumbers[0].number.replace(/\s|-/g, '');
    const timeStr = appointmentTime.toTimeString().slice(0, 5);

    set(ref(database, `appointments/${dateKey}/${id}`), {
      name: contactToSchedule.name,
      phone: cleanPhone,
      time: timeStr
    });

    setShowTimePicker(false);
    setContactToSchedule(null);
    setAppointmentTime(new Date());
  };

  const editAppointmentTime = (id) => {
    setEditingAppointmentId(id);
    setShowTimePicker(true);
  };

  const deleteAppointment = (id) => {
    remove(ref(database, `appointments/${dateKey}/${id}`));
  };

  const sendWhatsAppReminders = async () => {
    const triggerRef = ref(database, 'trigger/send_whatsapp');
    await set(triggerRef, {
      send_now: true,
      date: dateKey
    });
    Alert.alert("🚀 Trigger Sent", "WhatsApp reminder script will now run.");
  };

  const openSMS = (phone, name, time) => {
    const formattedPhone = phone.startsWith('+') ? phone : '+972' + phone.replace(/^0+/, '');
    const message = `שלום ${name}, תזכורת לתור שלך היום בשעה ${time}. תודה, רון הספר 💈`;
    const url = `sms:${formattedPhone}?body=${encodeURIComponent(message)}`;

    Linking.openURL(url).catch(err =>
      Alert.alert('Error', 'Could not open SMS app.')
    );
  };

  const filteredContacts = contacts.filter(c =>
    c.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <View style={styles.container}>
      <Text style={styles.header}>📅 Barber Schedule</Text>

      <View style={styles.dateRow}>
        <Text style={styles.label}>Selected Day:</Text>
        <StyledButton title={dateKey} onPress={() => setShowDatePicker(true)} color="#5B2C6F" />
      </View>

      {showDatePicker && (
        <DateTimePicker
          mode="date"
          value={selectedDate}
          onChange={(e, selected) => {
            setShowDatePicker(false);
            if (selected) setSelectedDate(selected);
          }}
        />
      )}

      <View style={styles.searchRow}>
        <StyledButton
          title={showContacts ? "Hide Contacts" : "Load Contacts"}
          onPress={() => showContacts ? setShowContacts(false) : loadContacts()}
          color="#2ecc71"
        />
        <TextInput
          placeholder="Search contact"
          value={searchTerm}
          onChangeText={setSearchTerm}
          style={styles.searchInput}
        />
      </View>

      {showContacts && (
        <FlatList
          data={filteredContacts}
          keyExtractor={(item) => item.id}
          style={styles.list}
          renderItem={({ item }) => (
            <TouchableOpacity style={styles.card} onPress={() => handleContactPress(item)}>
              <Text style={styles.cardText}>{item.name}</Text>
              <Text style={styles.cardSub}>{item.phoneNumbers[0].number}</Text>
            </TouchableOpacity>
          )}
        />
      )}

      {showTimePicker && (
        <DateTimePicker
          mode="time"
          is24Hour
          value={appointmentTime}
          onChange={(e, selected) => {
            if (selected) {
              setAppointmentTime(selected);
              if (editingAppointmentId) {
                update(ref(database, `appointments/${dateKey}/${editingAppointmentId}`), {
                  time: selected.toTimeString().slice(0, 5)
                });
                setEditingAppointmentId(null);
              } else {
                confirmTimeAndSave();
              }
              setShowTimePicker(false);
            } else {
              setShowTimePicker(false);
            }
          }}
        />
      )}

      <Text style={styles.subHeader}>📋 Appointments ({appointments.length})</Text>
      <FlatList
        data={appointments}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <View style={styles.card}>
            <Text style={styles.cardText}>{item.time} — {item.name}</Text>
            <Text style={styles.cardSub}>{item.phone}</Text>
            <View style={styles.actions}>
              <StyledButton title="Edit" onPress={() => editAppointmentTime(item.id)} color="#3498db" />
              <StyledButton title="Delete" onPress={() => deleteAppointment(item.id)} color="#E74C3C" />
              <StyledButton title="Send SMS" onPress={() => openSMS(item.phone, item.name, item.time)} color="#2ecc71" />
            </View>
          </View>
        )}
      />

      <View style={{ marginTop: 30 }}>
        <StyledButton title="Send Messages" onPress={sendWhatsAppReminders} color="#5B2C6F" />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { padding: 20, flex: 1, backgroundColor: '#F4F1FB' },
  header: { fontSize: 24, fontWeight: 'bold', textAlign: 'center', color: '#2C3E50', marginBottom: 15 },
  subHeader: { fontSize: 20, fontWeight: 'bold', marginTop: 20, color: '#2C3E50', marginBottom: 10 },
  label: { fontSize: 16, color: '#5B2C6F' },
  dateRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 },
  searchRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 10 },
  searchInput: { flex: 1, marginLeft: 10, borderBottomWidth: 2, borderColor: '#95A5A6', color: '#2C3E50' },
  list: { marginTop: 10 },
  card: { backgroundColor: '#FFFFFF', padding: 14, borderRadius: 12, marginBottom: 12, elevation: 3 },
  cardText: { fontSize: 16, fontWeight: '600', color: '#2C3E50' },
  cardSub: { color: '#95A5A6', fontSize: 14 },
  actions: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 12 }
});

const buttonStyles = StyleSheet.create({
  button: { paddingVertical: 10, paddingHorizontal: 14, borderRadius: 8, alignItems: 'center' },
  text: { color: '#fff', fontWeight: 'bold' }
});
